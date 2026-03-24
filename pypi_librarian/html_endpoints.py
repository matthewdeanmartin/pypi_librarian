# coding=utf-8
"""
PyPI HTML scraping endpoints.

PEP 503 Simple Repository API:
  GET /simple/   — full list of all package names

User profile pages:
  GET /user/<username>/  — packages maintained by a user
"""

from __future__ import annotations

from typing import Iterator

import requests
from lxml import html

__all__ = ["HtmlEndpoints"]


class HtmlEndpoints:
    """HTML scraping of pypi.org pages."""

    def project_page(self, name: str) -> str:
        """Fetch raw HTML of a project page."""
        response = requests.get(f"https://pypi.org/project/{name}/")
        response.raise_for_status()
        return response.text

    def user_page(self, name: str) -> str:
        """Fetch raw HTML of a user profile page."""
        response = requests.get(f"https://pypi.org/user/{name}/")
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
        response = requests.get("https://pypi.org/simple/")
        response.raise_for_status()
        tree = html.fromstring(response.content)
        yield from tree.xpath("//a/text()")
