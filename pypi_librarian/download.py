# coding=utf-8
"""
Download PyPI distribution files (wheels, sdists) with checksum verification.

Supports single-package and bulk async downloads with:
- SHA256 checksum verification against PyPI-provided digests
- Bounded concurrency via asyncio Semaphore
- Resume via NDJSON checkpoint file (skip already-downloaded packages)
- Rate limiting via token bucket
- Sync wrappers for callers who don't need async

Usage::

    from pypi_librarian.download import Downloader

    dl = Downloader(dest_dir="./packages")
    result = dl.download_one_sync("requests")

    # Bulk:
    results = dl.download_many_sync(["requests", "flask", "django"])

    # Resume an interrupted bulk download:
    results = dl.go_or_resume_sync(["requests", "flask", "django"])
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from pypi_librarian.json_endpoints import AsyncJsonEndpoints
from pypi_librarian.rate_limit import RateLimiter
from pypi_librarian.utils import run_async

__all__ = ["DownloadPolicy", "DownloadResult", "Downloader"]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DownloadPolicy:
    """Configuration for how files are downloaded and handled.

    Args:
        file_types: Which distribution types to download.
            Valid values: ``"bdist_wheel"``, ``"sdist"``, or ``"all"``.
        max_workers: Maximum concurrent downloads.
        rate_limit: Maximum HTTP requests per second (0 = unlimited).
        verify_checksums: Whether to verify SHA256 after download.
    """

    file_types: list[str] = field(default_factory=lambda: ["bdist_wheel", "sdist"])
    max_workers: int = 10
    rate_limit: float = 10.0
    verify_checksums: bool = True


@dataclass
class DownloadResult:
    """Outcome of downloading one package (possibly multiple files).

    Attributes:
        name: Package name.
        version: Version that was downloaded.
        files: List of successfully downloaded file paths.
        errors: List of error messages for files that failed.
        skipped: List of filenames skipped (wrong type, already exists, etc.).
        checksum_ok: True if all downloaded files passed SHA256 verification.
    """

    name: str
    version: str
    files: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    checksum_ok: bool = True


# ---------------------------------------------------------------------------
# Checkpoint persistence (NDJSON)
# ---------------------------------------------------------------------------


class _Checkpoint:
    """Track completed downloads in an append-only NDJSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._done: set[str] = set()
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        key = f"{record['name']}=={record['version']}"
                        self._done.add(key)
                    except (json.JSONDecodeError, KeyError):
                        continue
            logger.info("Checkpoint: %d packages already done", len(self._done))

    def is_done(self, name: str, version: str) -> bool:
        return f"{name}=={version}" in self._done

    def mark_done(self, result: DownloadResult) -> None:
        key = f"{result.name}=={result.version}"
        if key in self._done:
            return
        self._done.add(key)
        record = {
            "name": result.name,
            "version": result.version,
            "files": result.files,
            "errors": result.errors,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")


# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------


class Downloader:
    """
    Download PyPI distribution files with checksum verification.

    Args:
        dest_dir: Directory to save downloaded files into.
        policy: Download configuration.  Defaults to downloading wheels
            and sdists, 10 concurrent workers, 10 req/s rate limit.
        base_url: PyPI base URL.
    """

    def __init__(
        self,
        dest_dir: str | Path = ".",
        policy: DownloadPolicy | None = None,
        base_url: str = "https://pypi.org",
    ) -> None:
        self.dest_dir = Path(dest_dir)
        self.policy = policy or DownloadPolicy()
        self.base_url = base_url.rstrip("/")
        self._checkpoint_path = self.dest_dir / ".pypi_checkpoint.ndjson"

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def download_one(
        self, name: str, version: str | None = None
    ) -> DownloadResult:
        """
        Download distribution files for a single package.

        If *version* is ``None``, downloads the latest version.
        Returns a :class:`DownloadResult` with file paths and any errors.
        """
        self.dest_dir.mkdir(parents=True, exist_ok=True)

        api = AsyncJsonEndpoints(repo_url=f"{self.base_url}/pypi")
        limiter = (
            RateLimiter(rate=self.policy.rate_limit)
            if self.policy.rate_limit > 0
            else None
        )

        try:
            if version:
                data = await api.package_version_json(name, version)
            else:
                data = await api.package_json(name)

            if data is None:
                ver = f"{version}" if version else "latest"
                return DownloadResult(
                    name=name,
                    version=ver,
                    errors=[f"Package {name!r} (version {ver}) not found on PyPI"],
                )

            actual_version = data["info"]["version"]
            files_data = data.get("urls") or []

            return await self._download_files(name, actual_version, files_data, limiter)
        finally:
            await api.close()

    async def download_many(
        self, names: list[str], versions: dict[str, str] | None = None
    ) -> list[DownloadResult]:
        """
        Download distribution files for multiple packages concurrently.

        Args:
            names: Package names to download.
            versions: Optional mapping of name -> version.  If a name is
                not in the mapping, the latest version is downloaded.

        Returns a list of :class:`DownloadResult` — one per package.
        Failed packages do not abort the batch.
        """
        versions = versions or {}
        sem = asyncio.Semaphore(self.policy.max_workers)

        async def _one(pkg_name: str) -> DownloadResult:
            async with sem:
                return await self.download_one(pkg_name, versions.get(pkg_name))

        results = await asyncio.gather(
            *[_one(n) for n in names], return_exceptions=True
        )
        out: list[DownloadResult] = []
        for name, result in zip(names, results):
            if isinstance(result, BaseException):
                out.append(
                    DownloadResult(
                        name=name,
                        version=versions.get(name, "latest"),
                        errors=[f"{type(result).__name__}: {result}"],
                    )
                )
            else:
                out.append(result)
        return out

    async def go_or_resume(
        self, names: list[str], versions: dict[str, str] | None = None
    ) -> list[DownloadResult]:
        """
        Download packages, skipping those already completed per checkpoint.

        Reads the checkpoint file in *dest_dir*, skips done packages,
        downloads the rest, and appends results to the checkpoint.
        """
        self.dest_dir.mkdir(parents=True, exist_ok=True)
        versions = versions or {}
        checkpoint = _Checkpoint(self._checkpoint_path)

        # Resolve versions for packages we need to check
        api = AsyncJsonEndpoints(repo_url=f"{self.base_url}/pypi")
        todo_names: list[str] = []
        todo_versions: dict[str, str] = {}
        skipped_results: list[DownloadResult] = []

        try:
            for name in names:
                ver = versions.get(name)
                if ver and checkpoint.is_done(name, ver):
                    skipped_results.append(
                        DownloadResult(name=name, version=ver, skipped=["checkpoint"])
                    )
                    continue
                if not ver:
                    # Need to resolve latest version to check checkpoint
                    data = await api.package_json(name)
                    if data is None:
                        skipped_results.append(
                            DownloadResult(
                                name=name,
                                version="unknown",
                                errors=[f"Package {name!r} not found"],
                            )
                        )
                        continue
                    ver = data["info"]["version"]
                    if checkpoint.is_done(name, ver):
                        skipped_results.append(
                            DownloadResult(
                                name=name, version=ver, skipped=["checkpoint"]
                            )
                        )
                        continue
                todo_names.append(name)
                todo_versions[name] = ver
        finally:
            await api.close()

        logger.info(
            "Checkpoint: %d skipped, %d to download",
            len(skipped_results),
            len(todo_names),
        )

        new_results = await self.download_many(todo_names, todo_versions)
        for result in new_results:
            if result.files and not result.errors:
                checkpoint.mark_done(result)

        return skipped_results + new_results

    # ------------------------------------------------------------------
    # Sync wrappers
    # ------------------------------------------------------------------

    def download_one_sync(
        self, name: str, version: str | None = None
    ) -> DownloadResult:
        """Sync wrapper for :meth:`download_one`."""
        return run_async(self.download_one(name, version))

    def download_many_sync(
        self, names: list[str], versions: dict[str, str] | None = None
    ) -> list[DownloadResult]:
        """Sync wrapper for :meth:`download_many`."""
        return run_async(self.download_many(names, versions))

    def go_or_resume_sync(
        self, names: list[str], versions: dict[str, str] | None = None
    ) -> list[DownloadResult]:
        """Sync wrapper for :meth:`go_or_resume`."""
        return run_async(self.go_or_resume(names, versions))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _download_files(
        self,
        name: str,
        version: str,
        files_data: list[dict[str, Any]],
        limiter: RateLimiter | None,
    ) -> DownloadResult:
        result = DownloadResult(name=name, version=version)
        pkg_dir = self.dest_dir / name / version
        pkg_dir.mkdir(parents=True, exist_ok=True)

        for file_info in files_data:
            filename = file_info["filename"]
            packagetype = file_info.get("packagetype", "")

            # Filter by policy
            if (
                "all" not in self.policy.file_types
                and packagetype not in self.policy.file_types
            ):
                result.skipped.append(filename)
                continue

            dest_path = pkg_dir / filename

            # Skip already-downloaded files
            if dest_path.exists():
                result.skipped.append(filename)
                continue

            url = file_info["url"]
            expected_sha256 = (file_info.get("digests") or {}).get("sha256", "")

            try:
                if limiter:
                    await limiter.acquire()
                await self._download_file(url, dest_path, expected_sha256)
                result.files.append(str(dest_path))
            except _ChecksumMismatch as exc:
                result.checksum_ok = False
                result.errors.append(f"{filename}: {exc}")
                # Remove the bad file
                if dest_path.exists():
                    dest_path.unlink()
            except Exception as exc:
                result.errors.append(f"{filename}: {type(exc).__name__}: {exc}")

        return result

    async def _download_file(self, url: str, dest: Path, expected_sha256: str) -> None:
        """Download a single file and verify its SHA256 checksum."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                sha256 = hashlib.sha256()
                with open(dest, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=65536):
                        f.write(chunk)
                        sha256.update(chunk)

        if self.policy.verify_checksums and expected_sha256:
            actual = sha256.hexdigest()
            if actual != expected_sha256:
                raise _ChecksumMismatch(
                    f"SHA256 mismatch: expected {expected_sha256}, got {actual}"
                )
            logger.debug("Checksum OK: %s", dest.name)


class _ChecksumMismatch(Exception):
    """Raised when a downloaded file fails SHA256 verification."""
