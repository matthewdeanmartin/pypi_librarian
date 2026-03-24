# coding=utf-8
"""
PyPI HTML scraping endpoints.

PEP 503 Simple Repository API:
  GET /simple/   — full list of all package names

User profile pages:
  GET /user/<username>/  — packages maintained by a user

Provides both sync (``HtmlEndpoints``) and async (``AsyncHtmlEndpoints``)
classes.
"""

from __future__ import annotations

from typing import AsyncIterator, Iterator

import httpx
from lxml import html

__all__ = ["AsyncHtmlEndpoints", "HtmlEndpoints"]


class HtmlEndpoints:
    """HTML scraping of pypi.org pages (sync, backed by ``httpx.Client``)."""

    def __init__(self) -> None:
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=60.0)
        return self._client

    def project_page(self, name: str) -> str:
        """Fetch raw HTML of a project page."""
        response = self._get_client().get(f"https://pypi.org/project/{name}/")
        response.raise_for_status()
        return response.text

    def user_page(self, name: str) -> str:
        """Fetch raw HTML of a user profile page."""
        response = self._get_client().get(f"https://pypi.org/user/{name}/")
        response.raise_for_status()
        return response.text

    def packages_for_user(self, name: str) -> list[str]:
        """
        Return a deduplicated list of package names maintained by *name*.

        Uses the PyPI XML-RPC ``user_packages`` method, which returns a list of
        ``[role, package_name]`` pairs.  The HTML user profile page is blocked
        by PyPI's bot-protection and cannot be scraped with plain HTTP.

        Returns an empty list if the user has no packages or does not exist.
        """
        import xmlrpc.client

        client = xmlrpc.client.ServerProxy("https://pypi.org/pypi")
        try:
            pairs = client.user_packages(name)
        except Exception:
            return []
        seen: set[str] = set()
        packages: list[str] = []
        for _role, pkg_name in pairs:
            if pkg_name and pkg_name not in seen:
                seen.add(pkg_name)
                packages.append(pkg_name)
        return packages

    def all(self) -> Iterator[str]:
        """
        Yield every package name registered on PyPI.

        Uses the PEP 503 Simple Repository API (``/simple/``), which is the
        recommended programmatic endpoint for enumerating all packages.
        """
        response = self._get_client().get("https://pypi.org/simple/")
        response.raise_for_status()
        tree = html.fromstring(response.content)
        yield from tree.xpath("//a/text()")

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None


class AsyncHtmlEndpoints:
    """Async HTML scraping of pypi.org pages (backed by ``httpx.AsyncClient``)."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=60.0)
        return self._client

    async def all_async(self) -> AsyncIterator[str]:
        """
        Yield every package name registered on PyPI (async).

        Uses the PEP 503 Simple Repository API (``/simple/``).
        """
        response = await self._get_client().get("https://pypi.org/simple/")
        response.raise_for_status()
        tree = html.fromstring(response.content)
        for name in tree.xpath("//a/text()"):
            yield name

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
