# coding=utf-8
"""
Unit tests for pypi_librarian.github.

All tests mock HTTP via pytest-httpx — no network access required.
"""

from __future__ import annotations

import pytest
import httpx
from pytest_httpx import HTTPXMock

from pypi_librarian.github import (
    GitHubInfo,
    extract_github_repo,
    fetch_github_info,
    fetch_github_info_for_project,
)


_REPO_RESPONSE = {
    "id": 12345,
    "name": "requests",
    "full_name": "psf/requests",
    "owner": {"login": "psf"},
    "description": "A simple, yet elegant HTTP library.",
    "stargazers_count": 51000,
    "forks_count": 9000,
    "open_issues_count": 300,
    "pushed_at": "2024-03-01T10:00:00Z",
    "archived": False,
}


# ---------------------------------------------------------------------------
# extract_github_repo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "project_url, home_page, expected",
    [
        ("https://github.com/psf/requests", None, ("psf", "requests")),
        ("https://github.com/psf/requests/", None, ("psf", "requests")),
        ("https://github.com/psf/requests.git", None, ("psf", "requests")),
        (None, "https://github.com/psf/requests", ("psf", "requests")),
        ("https://example.com", "https://github.com/psf/requests", ("psf", "requests")),
        (None, None, None),
        ("https://example.com", None, None),
        ("https://gitlab.com/psf/requests", None, None),
    ],
)
def test_extract_github_repo(project_url, home_page, expected) -> None:
    assert extract_github_repo(project_url, home_page) == expected


# ---------------------------------------------------------------------------
# fetch_github_info
# ---------------------------------------------------------------------------


def test_fetch_github_info_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/psf/requests",
        json=_REPO_RESPONSE,
    )
    info = fetch_github_info("psf", "requests")
    assert isinstance(info, GitHubInfo)
    assert info.owner == "psf"
    assert info.repo == "requests"
    assert info.stars == 51000
    assert info.forks == 9000
    assert info.open_issues == 300
    assert info.last_push == "2024-03-01T10:00:00Z"
    assert info.description == "A simple, yet elegant HTTP library."
    assert info.archived is False


def test_fetch_github_info_not_found(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/nobody/no-such-repo",
        status_code=404,
    )
    result = fetch_github_info("nobody", "no-such-repo")
    assert result is None


def test_fetch_github_info_rate_limited(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/psf/requests",
        status_code=403,
    )
    result = fetch_github_info("psf", "requests")
    assert result is None


def test_fetch_github_info_archived(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/owner/old-lib",
        json={**_REPO_RESPONSE, "archived": True, "name": "old-lib", "full_name": "owner/old-lib"},
    )
    info = fetch_github_info("owner", "old-lib")
    assert info is not None
    assert info.archived is True


def test_fetch_github_info_raw_preserved(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/psf/requests",
        json=_REPO_RESPONSE,
    )
    info = fetch_github_info("psf", "requests")
    assert info is not None
    assert info.raw["id"] == 12345


# ---------------------------------------------------------------------------
# fetch_github_info_for_project
# ---------------------------------------------------------------------------


def test_fetch_github_info_for_project_no_url() -> None:
    result = fetch_github_info_for_project(None, None)
    assert result is None


def test_fetch_github_info_for_project_non_github_url() -> None:
    result = fetch_github_info_for_project("https://example.com", None)
    assert result is None


def test_fetch_github_info_for_project_success(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url="https://api.github.com/repos/psf/requests",
        json=_REPO_RESPONSE,
    )
    info = fetch_github_info_for_project(
        "https://github.com/psf/requests", None
    )
    assert info is not None
    assert info.stars == 51000
