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
"""

from __future__ import annotations

from typing import Iterator

from pypi_librarian.html_endpoints import HtmlEndpoints
from pypi_librarian.json_endpoints import JsonEndpoints
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

__all__ = ["Repository"]


class Repository:
    """
    Access PyPI data.  Wraps the JSON API, Simple HTML API, and RSS feeds.

    Args:
        base_url: Root URL of the PyPI instance.  Defaults to
            ``https://pypi.org``.  Can be pointed at a compatible mirror.
    """

    def __init__(self, base_url: str = "https://pypi.org") -> None:
        self.base_url = base_url.rstrip("/")
        self._json = JsonEndpoints(repo_url=f"{self.base_url}/pypi")
        self._html = HtmlEndpoints()
        self._rss = RssEndpoints()

    # ------------------------------------------------------------------
    # Single-object queries
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
    # Feed queries
    # ------------------------------------------------------------------

    def newest_packages(self, count: int = 40) -> list[NewPackage]:
        """Return the most recently created packages from the RSS feed."""
        return self._rss.newest_packages()[:count]

    def latest_updates(self, count: int = 40) -> list[NewRelease]:
        """Return the most recently updated packages from the RSS feed."""
        return self._rss.latest_updates()[:count]

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
