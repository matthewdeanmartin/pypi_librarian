# coding=utf-8
"""
Unit tests for pypi_librarian.pypistats.

All tests mock HTTP via pytest-httpx2 — no network access required.
"""

from __future__ import annotations

import json

import httpx2
import pytest
from pytest_httpx2 import HTTPXMock

from pypi_librarian.pypistats import DownloadStats, fetch_download_stats

_RECENT_RESPONSE = {
    "data": [
        {"category": "last_day", "downloads": 12345},
        {"category": "last_week", "downloads": 87654},
        {"category": "last_month", "downloads": 345678},
    ],
    "package": "requests",
    "type": "recent_downloads",
}


def test_fetch_download_stats_success(httpx2_mock: HTTPXMock) -> None:
    httpx2_mock.add_response(
        url="https://pypistats.org/api/packages/requests/recent",
        json=_RECENT_RESPONSE,
    )
    stats = fetch_download_stats("requests")
    assert isinstance(stats, DownloadStats)
    assert stats.package == "requests"
    assert stats.last_day == 12345
    assert stats.last_week == 87654
    assert stats.last_month == 345678


def test_fetch_download_stats_not_found(httpx2_mock: HTTPXMock) -> None:
    httpx2_mock.add_response(
        url="https://pypistats.org/api/packages/no-such-package-xyz/recent",
        status_code=404,
    )
    result = fetch_download_stats("no-such-package-xyz")
    assert result is None


def test_fetch_download_stats_reuses_client(httpx2_mock: HTTPXMock) -> None:
    httpx2_mock.add_response(
        url="https://pypistats.org/api/packages/flask/recent",
        json={
            "data": [
                {"category": "last_day", "downloads": 1},
                {"category": "last_week", "downloads": 7},
                {"category": "last_month", "downloads": 30},
            ],
            "package": "flask",
        },
    )
    with httpx2.Client() as client:
        stats = fetch_download_stats("flask", client=client)
    assert stats is not None
    assert stats.last_month == 30


def test_fetch_download_stats_raw_preserved(httpx2_mock: HTTPXMock) -> None:
    httpx2_mock.add_response(
        url="https://pypistats.org/api/packages/requests/recent",
        json=_RECENT_RESPONSE,
    )
    stats = fetch_download_stats("requests")
    assert stats is not None
    assert stats.raw == _RECENT_RESPONSE


def test_fetch_download_stats_missing_categories(httpx2_mock: HTTPXMock) -> None:
    """Partial response — missing categories should default to 0."""
    httpx2_mock.add_response(
        url="https://pypistats.org/api/packages/tiny/recent",
        json={"data": [{"category": "last_month", "downloads": 5}], "package": "tiny"},
    )
    stats = fetch_download_stats("tiny")
    assert stats is not None
    assert stats.last_day == 0
    assert stats.last_week == 0
    assert stats.last_month == 5
