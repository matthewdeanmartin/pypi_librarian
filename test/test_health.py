# coding=utf-8
"""
Unit tests for pypi_librarian.health.

No network access — all inputs are constructed inline.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from pypi_librarian.github import GitHubInfo
from pypi_librarian.health import HealthScore, _parse_date, _within_days, score_project
from pypi_librarian.models import ProjectInfo
from pypi_librarian.pypistats import DownloadStats


def _make_info(**overrides) -> ProjectInfo:
    defaults = dict(
        name="test-pkg",
        version="1.0.0",
        summary="A great package",
        author="Alice",
        author_email="alice@example.com",
        maintainer=None,
        maintainer_email=None,
        license="MIT",
        home_page="https://github.com/alice/test-pkg",
        project_url="https://github.com/alice/test-pkg",
        requires_python=">=3.10",
        classifiers=("License :: OSI Approved :: MIT License",),
        keywords="test",
        description="Long description.",
        description_content_type="text/markdown",
        requires_dist=("requests>=2.0",),
        yanked=False,
        yanked_reason=None,
        raw={},
    )
    defaults.update(overrides)
    return ProjectInfo(**defaults)


def _recent_ts() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )


def _old_ts() -> str:
    return "2018-01-01T00:00:00"


# ---------------------------------------------------------------------------
# Perfect package — should score 1.0
# ---------------------------------------------------------------------------


def test_perfect_score() -> None:
    info = _make_info()
    stats = DownloadStats(
        package="test-pkg", last_day=1, last_week=7, last_month=100, raw={}
    )
    github = GitHubInfo(
        owner="alice",
        repo="test-pkg",
        stars=500,
        forks=50,
        open_issues=10,
        last_push=_recent_ts(),
        description="A great package",
        archived=False,
        raw={},
    )
    result = score_project(
        info, releases_upload_times=[_recent_ts()], stats=stats, github=github
    )
    assert isinstance(result, HealthScore)
    assert result.score == 1.0
    assert result.notes == []


# ---------------------------------------------------------------------------
# Missing optional enrichment — score is still normalised correctly
# ---------------------------------------------------------------------------


def test_score_without_enrichment() -> None:
    info = _make_info()
    result = score_project(info, releases_upload_times=[_recent_ts()])
    # Without stats and github the max achievable excludes those weights.
    # All base components should pass → score == 1.0
    assert result.score == 1.0


def test_score_no_summary() -> None:
    info = _make_info(summary=None)
    result = score_project(info, releases_upload_times=[_recent_ts()])
    assert result.score < 1.0
    assert any("summary" in n.lower() for n in result.notes)


def test_score_no_classifiers() -> None:
    info = _make_info(classifiers=())
    result = score_project(info, releases_upload_times=[_recent_ts()])
    assert result.score < 1.0
    assert any("classifier" in n.lower() for n in result.notes)


def test_score_no_license() -> None:
    info = _make_info(license=None)
    result = score_project(info, releases_upload_times=[_recent_ts()])
    assert result.score < 1.0
    assert any("license" in n.lower() for n in result.notes)


def test_score_old_requires_python() -> None:
    info = _make_info(requires_python=">=2.7")
    result = score_project(info, releases_upload_times=[_recent_ts()])
    assert result.score < 1.0
    assert any("python" in n.lower() for n in result.notes)


def test_score_no_requires_python() -> None:
    info = _make_info(requires_python=None)
    result = score_project(info, releases_upload_times=[_recent_ts()])
    assert result.score < 1.0


def test_score_yanked() -> None:
    info = _make_info(yanked=True, yanked_reason="security issue")
    result = score_project(info, releases_upload_times=[_recent_ts()])
    assert result.score < 1.0
    assert any("yanked" in n.lower() for n in result.notes)


def test_score_stale_releases() -> None:
    info = _make_info()
    result = score_project(info, releases_upload_times=[_old_ts()])
    assert result.score < 1.0
    assert any("release" in n.lower() for n in result.notes)


def test_score_zero_downloads() -> None:
    info = _make_info()
    stats = DownloadStats(
        package="test-pkg", last_day=0, last_week=0, last_month=0, raw={}
    )
    result = score_project(info, releases_upload_times=[_recent_ts()], stats=stats)
    assert result.score < 1.0
    assert any("download" in n.lower() for n in result.notes)


def test_score_archived_github() -> None:
    info = _make_info()
    github = GitHubInfo(
        owner="alice",
        repo="test-pkg",
        stars=10,
        forks=1,
        open_issues=0,
        last_push=_old_ts(),
        description="old",
        archived=True,
        raw={},
    )
    result = score_project(info, releases_upload_times=[_recent_ts()], github=github)
    assert result.score < 1.0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def test_parse_date_valid() -> None:

    dt = _parse_date("2024-03-15T10:00:00Z")
    assert dt is not None
    assert dt.year == 2024


def test_parse_date_invalid() -> None:

    assert _parse_date("not-a-date") is None
    assert _parse_date("") is None


def test_within_days_recent() -> None:
    ts = _recent_ts()
    assert _within_days(ts, 365) is True


def test_within_days_old() -> None:
    assert _within_days("2010-01-01T00:00:00", 730) is False
