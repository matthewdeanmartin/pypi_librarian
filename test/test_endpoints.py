# coding=utf-8
"""
Tests for the endpoint layer (JsonEndpoints, HtmlEndpoints, RssEndpoints).

Unit tests mock HTTP with unittest.mock; integration tests hit live PyPI.
Run only unit tests with:  pytest -m "not integration"
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from pypi_librarian.html_endpoints import HtmlEndpoints
from pypi_librarian.json_endpoints import JsonEndpoints
from pypi_librarian.models import NewPackage, NewRelease
from pypi_librarian.rss_endpoints import RssEndpoints


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_response(body: str, status: int = 200):
    mock = MagicMock()
    mock.status_code = status
    mock.text = body
    mock.content = body.encode()
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# JsonEndpoints — unit tests
# ---------------------------------------------------------------------------


class TestJsonEndpoints:
    def test_package_json_returns_dict(self, sample_project_json):
        je = JsonEndpoints()
        with patch.object(je, "_session_get", return_value=_mock_response(json.dumps(sample_project_json))):
            result = je.package_json("test-pkg")
        assert isinstance(result, dict)
        assert result["info"]["name"] == "test-pkg"

    def test_package_json_404_returns_none(self):
        je = JsonEndpoints()
        with patch.object(je, "_session_get", return_value=_mock_response("", status=404)):
            assert je.package_json("no-such-package") is None

    def test_package_version_json_returns_dict(self, sample_project_json):
        je = JsonEndpoints()
        with patch.object(je, "_session_get", return_value=_mock_response(json.dumps(sample_project_json))):
            result = je.package_version_json("test-pkg", "1.0.0")
        assert isinstance(result, dict)

    def test_package_version_json_404_returns_none(self):
        """Regression test: old code crashed on 404 by calling json.loads on empty string."""
        je = JsonEndpoints()
        with patch.object(je, "_session_get", return_value=_mock_response("", status=404)):
            assert je.package_version_json("test-pkg", "99.99.99") is None

    def test_package_json_as_text_returns_string(self, sample_project_json):
        je = JsonEndpoints()
        body = json.dumps(sample_project_json)
        with patch.object(je, "_session_get", return_value=_mock_response(body)):
            result = je.package_json_as_text("test-pkg")
        assert isinstance(result, str)
        assert "test-pkg" in result

    def test_package_json_as_text_404_returns_none(self):
        je = JsonEndpoints()
        with patch.object(je, "_session_get", return_value=_mock_response("", status=404)):
            assert je.package_json_as_text("no-such-package") is None


# ---------------------------------------------------------------------------
# HtmlEndpoints — unit tests
# ---------------------------------------------------------------------------


class TestHtmlEndpoints:
    def test_all_returns_strings(self):
        minimal_simple_html = b"<html><body><a href='/simple/requests/'>requests</a></body></html>"
        mock = _mock_response("")
        mock.content = minimal_simple_html
        hep = HtmlEndpoints()
        with patch("pypi_librarian.html_endpoints.requests.get", return_value=mock):
            names = list(hep.all())
        assert "requests" in names

    def test_packages_for_user_returns_list(self):
        hep = HtmlEndpoints()
        mock_client = MagicMock()
        mock_client.user_packages.return_value = [
            ["Owner", "alpha"],
            ["Maintainer", "beta"],
        ]
        with patch("xmlrpc.client.ServerProxy", return_value=mock_client):
            packages = hep.packages_for_user("testuser")
        assert "alpha" in packages
        assert "beta" in packages

    def test_packages_for_user_deduplicates(self):
        hep = HtmlEndpoints()
        mock_client = MagicMock()
        mock_client.user_packages.return_value = [
            ["Owner", "alpha"],
            ["Maintainer", "alpha"],  # duplicate
            ["Owner", "beta"],
        ]
        with patch("xmlrpc.client.ServerProxy", return_value=mock_client):
            packages = hep.packages_for_user("testuser")
        assert packages.count("alpha") == 1

    def test_packages_for_user_error_returns_empty_list(self):
        hep = HtmlEndpoints()
        mock_client = MagicMock()
        mock_client.user_packages.side_effect = Exception("network error")
        with patch("xmlrpc.client.ServerProxy", return_value=mock_client):
            packages = hep.packages_for_user("no-such-user")
        assert packages == []


# ---------------------------------------------------------------------------
# RssEndpoints — unit tests
# ---------------------------------------------------------------------------


class TestRssEndpoints:
    def test_newest_packages_returns_new_package_list(self, sample_rss_packages_xml):
        rss = RssEndpoints()
        with patch.object(rss, "_fetch", return_value=sample_rss_packages_xml):
            result = rss.newest_packages()
        assert isinstance(result, list)
        assert all(isinstance(p, NewPackage) for p in result)

    def test_latest_updates_returns_new_release_list(self, sample_rss_updates_xml):
        rss = RssEndpoints()
        with patch.object(rss, "_fetch", return_value=sample_rss_updates_xml):
            result = rss.latest_updates()
        assert isinstance(result, list)
        assert all(isinstance(r, NewRelease) for r in result)

    def test_newest_packages_raw_returns_string(self, sample_rss_packages_xml):
        rss = RssEndpoints()
        with patch.object(rss, "_fetch", return_value=sample_rss_packages_xml):
            result = rss.newest_packages_raw()
        assert isinstance(result, str)
        assert "<rss" in result

    def test_latest_updates_raw_returns_string(self, sample_rss_updates_xml):
        rss = RssEndpoints()
        with patch.object(rss, "_fetch", return_value=sample_rss_updates_xml):
            result = rss.latest_updates_raw()
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Integration tests — require live network access to PyPI
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_json_endpoints_live_requests():
    je = JsonEndpoints()
    data = je.package_json("requests")
    assert data is not None
    assert data["info"]["name"] == "requests"


@pytest.mark.integration
def test_json_endpoints_live_version():
    je = JsonEndpoints()
    data = je.package_version_json("requests", "2.28.0")
    assert data is not None
    assert data["info"]["version"] == "2.28.0"


@pytest.mark.integration
def test_json_endpoints_live_404_returns_none():
    je = JsonEndpoints()
    assert je.package_json("this-package-absolutely-does-not-exist-xyz-abc-123") is None


@pytest.mark.integration
def test_html_endpoints_live_simple():
    hep = HtmlEndpoints()
    names = list(name for name, _ in zip(hep.all(), range(3)))
    assert len(names) == 3
    assert all(isinstance(n, str) for n in names)


@pytest.mark.integration
def test_rss_endpoints_live_newest():
    rss = RssEndpoints()
    packages = rss.newest_packages()
    assert len(packages) > 0
    assert packages[0].title
    assert packages[0].link


@pytest.mark.integration
def test_rss_endpoints_live_updates():
    rss = RssEndpoints()
    updates = rss.latest_updates()
    assert len(updates) > 0
