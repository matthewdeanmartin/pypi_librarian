# coding=utf-8
"""
Edge case unit tests for pypi_librarian.health.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from pypi_librarian.health import _parse_date, score_project, _ISO_PREFIX, _RECENT_PY_RE
from pypi_librarian.models import ProjectInfo


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


class TestHealthEdgeCases:
    @pytest.mark.parametrize("ts, expected_year", [
        ("2024-01-01T12:00:00Z", 2024),
        ("2023-12-31T23:59:59.999", 2023),
        ("2022-05-20", 2022),
        ("2021-02-28 10:00:00", 2021),
    ])
    def test_parse_date_various_iso8601(self, ts, expected_year):
        dt = _parse_date(ts)
        assert dt is not None
        assert dt.year == expected_year
        assert dt.tzinfo == timezone.utc

    @pytest.mark.parametrize("ts", [
        "not-a-date",
        "202-01-01",
        "2024/01/01",
        "01-01-2024",
    ])
    def test_parse_date_invalid_formats(self, ts):
        assert _parse_date(ts) is None

    @pytest.mark.parametrize("rp, expected_score_component", [
        (">=3.8", 0.15),
        (">= 3.9", 0.15),
        (">=3.12.0", 0.15),
        (">=3.7", 0.0),
        (">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*", 0.0),
        ("3.8", 0.0),  # Currently, the regex requires >=
        ("~=3.8", 0.0), # Currently, the regex requires >=
    ])
    def test_requires_python_recent_logic(self, rp, expected_score_component):
        # We're testing the logic inside score_project for requires_python_recent
        info = _make_info(requires_python=rp)
        # Note: score_project normalizes. We check the internal component directly if we could,
        # but here we'll just check if the final score reflects the presence/absence of this component.
        # Base components (summary, classifiers, license, not_yanked) = 0.10+0.10+0.10+0.10 = 0.40
        # requires_python_recent = 0.15
        # Total base = 0.55
        # Score = earned / 0.55
        # If earned = 0.40 + 0.15 = 0.55, score = 1.0
        # If earned = 0.40 + 0.00 = 0.40, score = 0.7272...
        result = score_project(info)
        if expected_score_component > 0:
            assert result.score == 1.0
        else:
            assert result.score < 1.0
            assert any("older Python" in n or "No requires_python" in n for n in result.notes)

    def test_score_project_empty_notes_on_perfect(self):
        info = _make_info(requires_python=">=3.8")
        result = score_project(info)
        assert result.notes == []

    def test_score_project_all_notes_on_worst(self):
        info = _make_info(summary="", classifiers=[], license="", requires_python=">=2.7", yanked=True)
        result = score_project(info)
        assert len(result.notes) >= 5
        assert "No package summary" in result.notes
        assert "No PyPI classifiers" in result.notes
        assert "No license declared" in result.notes
        assert "requires_python (>=2.7) targets older Python" in result.notes
        assert "Latest version is yanked" in result.notes
