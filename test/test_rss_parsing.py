# coding=utf-8
"""
Unit tests for RSS feed parsing — no network access required.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pypi_librarian.models import NewPackage, NewRelease
from pypi_librarian.rss_endpoints import RssEndpoints


@pytest.fixture()
def rss_client():
    return RssEndpoints()


# ---------------------------------------------------------------------------
# Newest-packages feed
# ---------------------------------------------------------------------------


def test_parse_new_packages_returns_list(rss_client, sample_rss_packages_xml):
    result = rss_client._parse_new_packages(sample_rss_packages_xml)
    assert isinstance(result, list)


def test_parse_new_packages_item_count(rss_client, sample_rss_packages_xml):
    result = rss_client._parse_new_packages(sample_rss_packages_xml)
    assert len(result) == 2


def test_parse_new_packages_returns_new_package_instances(rss_client, sample_rss_packages_xml):
    result = rss_client._parse_new_packages(sample_rss_packages_xml)
    assert all(isinstance(item, NewPackage) for item in result)


def test_parse_new_packages_first_item_fields(rss_client, sample_rss_packages_xml):
    result = rss_client._parse_new_packages(sample_rss_packages_xml)
    first = result[0]
    assert first.title == "mypackage 1.0.0"
    assert first.link == "https://pypi.org/project/mypackage/"
    assert first.description == "A shiny new package"
    assert "2024" in first.published


def test_parse_new_packages_raw_dict_populated(rss_client, sample_rss_packages_xml):
    result = rss_client._parse_new_packages(sample_rss_packages_xml)
    assert isinstance(result[0].raw, dict)
    assert len(result[0].raw) > 0


# ---------------------------------------------------------------------------
# Latest-updates feed
# ---------------------------------------------------------------------------


def test_parse_new_releases_returns_list(rss_client, sample_rss_updates_xml):
    result = rss_client._parse_new_releases(sample_rss_updates_xml)
    assert isinstance(result, list)


def test_parse_new_releases_returns_new_release_instances(rss_client, sample_rss_updates_xml):
    result = rss_client._parse_new_releases(sample_rss_updates_xml)
    assert all(isinstance(item, NewRelease) for item in result)


def test_parse_new_releases_item_count(rss_client, sample_rss_updates_xml):
    result = rss_client._parse_new_releases(sample_rss_updates_xml)
    assert len(result) == 1


def test_parse_new_releases_first_item_fields(rss_client, sample_rss_updates_xml):
    result = rss_client._parse_new_releases(sample_rss_updates_xml)
    first = result[0]
    assert first.title == "requests 2.32.0"
    assert "requests" in first.link
    assert first.description == "HTTP for Humans"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_parse_empty_channel_returns_empty_list(rss_client):
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty feed</title>
  </channel>
</rss>"""
    assert rss_client._parse_new_packages(xml) == []
    assert rss_client._parse_new_releases(xml) == []


def test_parse_malformed_xml_raises(rss_client):
    with pytest.raises(ET.ParseError):
        rss_client._parse_new_packages("<this is not xml")


def test_parse_item_with_missing_fields(rss_client):
    """Items with missing child elements produce empty strings, not exceptions."""
    xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>minimal 0.1</title>
    </item>
  </channel>
</rss>"""
    result = rss_client._parse_new_packages(xml)
    assert len(result) == 1
    assert result[0].title == "minimal 0.1"
    assert result[0].link == ""
    assert result[0].description == ""
    assert result[0].published == ""
