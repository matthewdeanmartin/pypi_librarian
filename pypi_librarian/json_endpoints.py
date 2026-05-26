# coding=utf-8
"""
PyPI JSON API endpoints.

Package level:   GET /pypi/<project_name>/json
Release level:   GET /pypi/<project_name>/<version>/json
Top 100 stats:   GET /stats/

Provides both sync (``JsonEndpoints``) and async (``AsyncJsonEndpoints``)
classes.  The sync class uses ``httpx.Client``; the async class uses
``httpx.AsyncClient``.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

__all__ = ["AsyncJsonEndpoints", "JsonEndpoints"]


class JsonEndpoints:
    """Synchronous PyPI JSON API client backed by ``httpx.Client``."""

    def __init__(self, repo_url: str = "https://pypi.org/pypi") -> None:
        self._client: httpx.Client | None = None
        self.index_url = repo_url.rstrip("/")

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def _session_get(self, *path: str) -> httpx.Response:
        url = self.index_url + "/" + "/".join(path)
        return self._get_client().get(url)

    def package_json(self, package: str) -> dict[str, Any] | None:
        """Return parsed JSON for the latest release, or None if not found."""
        response = self._session_get(package, "json")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return json.loads(response.text)

    def package_json_as_text(self, package: str) -> str | None:
        """Return raw JSON text for the latest release, or None if not found."""
        response = self._session_get(package, "json")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.text

    def package_version_json(self, package: str, version: str) -> dict[str, Any] | None:
        """Return parsed JSON for a specific version, or None if not found."""
        response = self._session_get(package, version, "json")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return json.loads(response.text)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None


class AsyncJsonEndpoints:
    """Async PyPI JSON API client backed by ``httpx.AsyncClient``."""

    def __init__(self, repo_url: str = "https://pypi.org/pypi") -> None:
        self._client: httpx.AsyncClient | None = None
        self.index_url = repo_url.rstrip("/")

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _get(self, *path: str) -> httpx.Response:
        url = self.index_url + "/" + "/".join(path)
        return await self._get_client().get(url)

    async def package_json(self, package: str) -> dict[str, Any] | None:
        """Return parsed JSON for the latest release, or None if not found."""
        response = await self._get(package, "json")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return json.loads(response.text)

    async def package_json_as_text(self, package: str) -> str | None:
        """Return raw JSON text for the latest release, or None if not found."""
        response = await self._get(package, "json")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.text

    async def package_version_json(
        self, package: str, version: str
    ) -> dict[str, Any] | None:
        """Return parsed JSON for a specific version, or None if not found."""
        response = await self._get(package, version, "json")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return json.loads(response.text)

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
