# coding=utf-8
"""
Bulk metadata fetcher — download JSON metadata for many packages.

Writes one ``.json`` file per package into a target directory.
Resume-safe: skips packages whose ``.json`` already exists.

Usage::

    from pypi_librarian.fetch_metadata import FetchMetadata

    fm = FetchMetadata(dest_dir="./metadata", limit=100)
    fm.run()  # sync — fetches up to 100 packages from /simple/

    # Or with an explicit package list:
    fm.run(names=["requests", "flask", "django"])
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Iterable

from pypi_librarian.html_endpoints import AsyncHtmlEndpoints
from pypi_librarian.json_endpoints import AsyncJsonEndpoints
from pypi_librarian.rate_limit import AsyncTokenBucket
from pypi_librarian.utils import run_async

__all__ = ["FetchMetadata"]

logger = logging.getLogger(__name__)

_DEFAULT_CONCURRENCY = 10
_DEFAULT_RATE = 10.0


class FetchMetadata:
    """
    Fetch and save JSON metadata for PyPI packages.

    Args:
        dest_dir: Directory to write ``<package>.json`` files into.
        limit: Maximum number of packages to fetch (0 = unlimited).
        max_workers: Concurrent HTTP requests.
        rate_limit: Maximum requests per second.
        base_url: PyPI base URL.
    """

    def __init__(
        self,
        dest_dir: str | Path = "metadata",
        limit: int = 0,
        max_workers: int = _DEFAULT_CONCURRENCY,
        rate_limit: float = _DEFAULT_RATE,
        base_url: str = "https://pypi.org",
    ) -> None:
        self.dest_dir = Path(dest_dir)
        self.limit = limit
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, names: Iterable[str] | None = None) -> int:
        """
        Fetch metadata (sync entry point).

        Args:
            names: Explicit list of package names.  If ``None``, all names
                are sourced from the Simple Repository API (``/simple/``).

        Returns the number of packages successfully fetched.
        """
        return run_async(self.run_async(names))

    async def run_async(self, names: Iterable[str] | None = None) -> int:
        """
        Fetch metadata (async entry point).

        Returns the number of packages successfully fetched.
        """
        self.dest_dir.mkdir(parents=True, exist_ok=True)
        done = self._already_done()
        logger.info("Already have %d packages in %s", len(done), self.dest_dir)

        if names is not None:
            todo = [n for n in names if n not in done]
        else:
            todo = await self._source_package_names(done)

        if self.limit > 0:
            todo = todo[: self.limit]

        if not todo:
            logger.info("Nothing to fetch")
            return 0

        logger.info("Fetching metadata for %d packages", len(todo))

        sem = asyncio.Semaphore(self.max_workers)
        bucket = AsyncTokenBucket(rate=self.rate_limit)
        api = AsyncJsonEndpoints(repo_url=f"{self.base_url}/pypi")
        count = 0

        async def _fetch_one(name: str) -> bool:
            async with sem:
                await bucket.acquire()
                try:
                    text = await api.package_json_as_text(name)
                except Exception as exc:
                    logger.warning("Failed to fetch %s: %s", name, exc)
                    return False

            if text is None:
                logger.debug("Package %s not found (404)", name)
                return False

            out_path = self.dest_dir / f"{name}.json"
            out_path.write_text(text, encoding="utf-8")
            return True

        try:
            results = await asyncio.gather(
                *[_fetch_one(n) for n in todo], return_exceptions=True
            )
        finally:
            await api.close()

        for name, result in zip(todo, results):
            if isinstance(result, BaseException):
                logger.warning("Error fetching %s: %s", name, result)
            elif result:
                count += 1

        logger.info("Fetched %d / %d packages", count, len(todo))
        return count

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _already_done(self) -> set[str]:
        """Return set of package names already fetched (have a .json file)."""
        if not self.dest_dir.exists():
            return set()
        return {
            f.stem
            for f in self.dest_dir.iterdir()
            if f.suffix == ".json" and f.is_file()
        }

    async def _source_package_names(self, done: set[str]) -> list[str]:
        """Fetch all package names from /simple/ and filter out already-done."""
        html_ep = AsyncHtmlEndpoints()
        try:
            todo: list[str] = []
            async for name in html_ep.all_async():
                if name not in done:
                    todo.append(name)
            return todo
        finally:
            await html_ep.close()
