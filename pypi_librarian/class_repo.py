# coding=utf-8
"""
Repository — the primary entry point for querying PyPI.

Typical usage::

    from pypi_librarian import Repository

    repo = Repository()
    project = repo.get_project("requests")
    print(project.info.version)
    print(project.info.summary)

    for release in project.releases:
        print(release.version, len(release.files))

Bulk async usage::

    from pypi_librarian.utils import run_async

    repo = Repository()
    projects = run_async(repo.get_many_projects_async(["requests", "flask"]))
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Iterator

from pypi_librarian.download import DownloadPolicy, DownloadResult, Downloader
from pypi_librarian.fetch_metadata import FetchMetadata
from pypi_librarian.html_endpoints import AsyncHtmlEndpoints, HtmlEndpoints
from pypi_librarian.json_endpoints import AsyncJsonEndpoints, JsonEndpoints
from pypi_librarian.models import (
    NewPackage,
    NewRelease,
    Package,
    Project,
    User,
    _package_from_json,
    _project_from_json,
)
from pypi_librarian.rss_endpoints import RssEndpoints
from pypi_librarian.utils import run_async

__all__ = ["Repository"]

_DEFAULT_CONCURRENCY = 10


class Repository:
    """
    Access PyPI data.  Wraps the JSON API, Simple HTML API, and RSS feeds.

    Args:
        base_url: Root URL of the PyPI instance.  Defaults to
            ``https://pypi.org``.  Can be pointed at a compatible mirror.
        max_concurrency: Maximum number of concurrent HTTP requests for
            bulk async operations.  Defaults to 10.
    """

    def __init__(
        self,
        base_url: str = "https://pypi.org",
        max_concurrency: int = _DEFAULT_CONCURRENCY,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.max_concurrency = max_concurrency
        self._json = JsonEndpoints(repo_url=f"{self.base_url}/pypi")
        self._html = HtmlEndpoints()
        self._rss = RssEndpoints()

    # ------------------------------------------------------------------
    # Single-object queries (sync)
    # ------------------------------------------------------------------

    def get_project(self, name: str) -> Project:
        """
        Fetch all metadata for *name* across every version.

        Returns a :class:`~pypi_librarian.models.Project` dataclass.

        Raises:
            ValueError: if the package does not exist on PyPI.
        """
        if not name:
            raise TypeError("Package name required")
        data = self._json.package_json(name)
        if data is None:
            raise ValueError(f"Package {name!r} not found on PyPI")
        return _project_from_json(data)

    def get_package(self, name: str, version: str) -> Package:
        """
        Fetch metadata for a specific *name* + *version*.

        Returns a :class:`~pypi_librarian.models.Package` dataclass.

        Raises:
            ValueError: if the package or version does not exist.
        """
        if not name:
            raise TypeError("Package name required")
        if not version:
            raise TypeError("Version required")
        data = self._json.package_version_json(name, version)
        if data is None:
            raise ValueError(f"Package {name!r} version {version!r} not found on PyPI")
        return _package_from_json(data)

    def get_user(self, name: str) -> User:
        """
        Fetch a user's profile and the list of packages they maintain.

        Returns a :class:`~pypi_librarian.models.User` dataclass.
        The ``packages`` field holds package name strings; call
        :meth:`get_project` on each if you need full metadata.
        """
        if not name:
            raise TypeError("User name required")
        packages = self._html.packages_for_user(name)
        return User(name=name, packages=packages)

    # ------------------------------------------------------------------
    # Enumeration
    # ------------------------------------------------------------------

    def get_all_package_names(self) -> Iterator[str]:
        """
        Yield every package name registered on PyPI.

        Backed by the PEP 503 Simple Repository API (``/simple/``).
        The full list is large (>600 k packages); iterate lazily.
        """
        yield from self._html.all()

    async def get_all_package_names_async(self) -> AsyncIterator[str]:
        """
        Yield every package name registered on PyPI (async).

        Backed by the PEP 503 Simple Repository API (``/simple/``).
        """
        async_html = AsyncHtmlEndpoints()
        try:
            async for name in async_html.all_async():
                yield name
        finally:
            await async_html.close()

    def project_names_by_user(self, name: str) -> list[str]:
        """Return the list of package names maintained by *name*."""
        if not name:
            raise TypeError("User name required")
        return self._html.packages_for_user(name)

    def projects_by_user(self, name: str) -> list[Project]:
        """
        Return full Project objects for every package maintained by *name*.

        Makes one HTTP request per package — use :meth:`project_names_by_user`
        if you only need the names.
        """
        if not name:
            raise TypeError("User name required")
        package_names = self._html.packages_for_user(name)
        projects = []
        for pkg_name in package_names:
            try:
                projects.append(self.get_project(pkg_name))
            except ValueError:
                # skip packages that were removed between scrape and fetch
                continue
        return projects

    # ------------------------------------------------------------------
    # Bulk async queries
    # ------------------------------------------------------------------

    async def get_many_projects_async(self, names: list[str]) -> list[Project]:
        """
        Fetch metadata for multiple packages concurrently.

        Returns a list of :class:`Project` objects in the same order as *names*.
        Packages that are not found on PyPI are silently skipped (the returned
        list may be shorter than the input).

        Uses :attr:`max_concurrency` to limit parallel requests.
        """
        sem = asyncio.Semaphore(self.max_concurrency)
        async_json = AsyncJsonEndpoints(repo_url=f"{self.base_url}/pypi")

        async def _fetch_one(name: str) -> Project | None:
            async with sem:
                data = await async_json.package_json(name)
            if data is None:
                return None
            return _project_from_json(data)

        try:
            results = await asyncio.gather(*[_fetch_one(n) for n in names])
        finally:
            await async_json.close()
        return [p for p in results if p is not None]

    def get_many_projects(self, names: list[str]) -> list[Project]:
        """
        Sync wrapper for :meth:`get_many_projects_async`.

        Uses :func:`~pypi_librarian.utils.run_async` so callers don't need
        to manage an event loop.
        """
        return run_async(self.get_many_projects_async(names))

    async def get_many_packages_async(
        self, items: list[tuple[str, str]]
    ) -> list[Package]:
        """
        Fetch metadata for multiple (name, version) pairs concurrently.

        Returns a list of :class:`Package` objects.  Pairs that are not found
        on PyPI are silently skipped.

        Uses :attr:`max_concurrency` to limit parallel requests.
        """
        sem = asyncio.Semaphore(self.max_concurrency)
        async_json = AsyncJsonEndpoints(repo_url=f"{self.base_url}/pypi")

        async def _fetch_one(name: str, version: str) -> Package | None:
            async with sem:
                data = await async_json.package_version_json(name, version)
            if data is None:
                return None
            return _package_from_json(data)

        try:
            results = await asyncio.gather(
                *[_fetch_one(n, v) for n, v in items]
            )
        finally:
            await async_json.close()
        return [p for p in results if p is not None]

    def get_many_packages(self, items: list[tuple[str, str]]) -> list[Package]:
        """
        Sync wrapper for :meth:`get_many_packages_async`.

        Uses :func:`~pypi_librarian.utils.run_async` so callers don't need
        to manage an event loop.
        """
        return run_async(self.get_many_packages_async(items))

    # ------------------------------------------------------------------
    # Feed queries
    # ------------------------------------------------------------------

    def newest_packages(self, count: int = 40) -> list[NewPackage]:
        """Return the most recently created packages from the RSS feed."""
        return self._rss.newest_packages()[:count]

    def latest_updates(self, count: int = 40) -> list[NewRelease]:
        """Return the most recently updated packages from the RSS feed."""
        return self._rss.latest_updates()[:count]

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(
        self,
        name: str,
        version: str | None = None,
        dest_dir: str = ".",
        policy: DownloadPolicy | None = None,
    ) -> DownloadResult:
        """
        Download distribution files for a single package.

        Args:
            name: Package name.
            version: Specific version, or ``None`` for latest.
            dest_dir: Directory to save files into.
            policy: Download configuration.

        Returns a :class:`~pypi_librarian.download.DownloadResult`.
        """
        dl = Downloader(dest_dir=dest_dir, policy=policy, base_url=self.base_url)
        return dl.download_one_sync(name, version)

    def download_many(
        self,
        names: list[str],
        dest_dir: str = ".",
        policy: DownloadPolicy | None = None,
        resume: bool = False,
    ) -> list[DownloadResult]:
        """
        Download distribution files for multiple packages.

        Args:
            names: Package names.
            dest_dir: Directory to save files into.
            policy: Download configuration.
            resume: If ``True``, skip packages completed in a previous run.

        Returns a list of :class:`~pypi_librarian.download.DownloadResult`.
        """
        dl = Downloader(dest_dir=dest_dir, policy=policy, base_url=self.base_url)
        if resume:
            return dl.go_or_resume_sync(names)
        return dl.download_many_sync(names)

    def fetch_metadata(
        self,
        dest_dir: str = "metadata",
        names: list[str] | None = None,
        limit: int = 0,
    ) -> int:
        """
        Fetch and save JSON metadata files for packages.

        Args:
            dest_dir: Directory to write ``.json`` files into.
            names: Explicit package list, or ``None`` to source from ``/simple/``.
            limit: Maximum packages to fetch (0 = unlimited).

        Returns the number of packages successfully fetched.
        """
        fm = FetchMetadata(
            dest_dir=dest_dir, limit=limit, base_url=self.base_url
        )
        return fm.run(names)

    # ------------------------------------------------------------------
    # Search (not available via public API)
    # ------------------------------------------------------------------

    def search_projects(self, query: str) -> list[Project]:  # noqa: ARG002
        """
        PyPI does not provide a public search API.

        Browse https://pypi.org/search/ manually, or use the ``warehouse``
        project's source to run your own search index.
        """
        raise NotImplementedError(
            "PyPI removed its public search API. "
            "Browse https://pypi.org/search/ manually."
        )
