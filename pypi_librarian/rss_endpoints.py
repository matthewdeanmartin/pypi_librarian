# coding=utf-8
"""
PyPI RSS feed endpoints.

Newest packages (brand-new projects):
  https://pypi.org/rss/packages.xml

Latest updates (new releases of existing projects):
  https://pypi.org/rss/updates.xml
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

from pypi_librarian.models import NewPackage, NewRelease
from pypi_librarian.models import _new_package_from_rss_item, _new_release_from_rss_item

__all__ = ["RssEndpoints"]

_NEWEST_URL = "https://pypi.org/rss/packages.xml"
_UPDATES_URL = "https://pypi.org/rss/updates.xml"


class RssEndpoints:
    """Typed wrappers around the PyPI RSS feeds."""

    def newest_packages(self) -> list[NewPackage]:
        """Return typed items from the newest-packages feed."""
        text = self._fetch(_NEWEST_URL)
        return self._parse_new_packages(text)

    def latest_updates(self) -> list[NewRelease]:
        """Return typed items from the latest-updates feed."""
        text = self._fetch(_UPDATES_URL)
        return self._parse_new_releases(text)

    def newest_packages_raw(self) -> str:
        """Return the raw RSS XML text for the newest-packages feed."""
        return self._fetch(_NEWEST_URL)

    def latest_updates_raw(self) -> str:
        """Return the raw RSS XML text for the latest-updates feed."""
        return self._fetch(_UPDATES_URL)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch(self, url: str) -> str:
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    def _parse_new_packages(self, xml_text: str) -> list[NewPackage]:
        root = ET.fromstring(xml_text)
        return [
            _new_package_from_rss_item(item)
            for item in root.findall("channel/item")
        ]

    def _parse_new_releases(self, xml_text: str) -> list[NewRelease]:
        root = ET.fromstring(xml_text)
        return [
            _new_release_from_rss_item(item)
            for item in root.findall("channel/item")
        ]
