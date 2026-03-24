# coding=utf-8
"""
PyPI JSON API endpoints.

Package level:   GET /pypi/<project_name>/json
Release level:   GET /pypi/<project_name>/<version>/json
Top 100 stats:   GET /stats/
"""

from __future__ import annotations

import json
from typing import Any

import requests

__all__ = ["JsonEndpoints"]


class JsonEndpoints:
    def __init__(self, repo_url: str = "https://pypi.org/pypi") -> None:
        self._session: requests.Session | None = None
        self.index_url = repo_url.rstrip("/")

    def _session_get(self, *path: str) -> requests.Response:
        if self._session is None:
            self._session = requests.Session()
        url = self.index_url + "/" + "/".join(path)
        return self._session.get(url)

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
