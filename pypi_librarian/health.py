# coding=utf-8
"""
Basic health / activity scoring for a PyPI package.

Produces a float score in the range [0.0, 1.0] based on a simple
weighted heuristic over fields that are already available in the
:class:`~pypi_librarian.models.ProjectInfo` and optional enrichment
data from :mod:`pypi_librarian.pypistats` and :mod:`pypi_librarian.github`.

This is intentionally a lightweight heuristic — not ML — so it is fast,
explainable, and has no extra dependencies.

Score components
----------------
- **has_summary** (0.10): ``info.summary`` is non-empty.
- **has_classifiers** (0.10): ``info.classifiers`` is non-empty.
- **has_license** (0.10): ``info.license`` is non-empty.
- **requires_python_recent** (0.15): ``requires_python`` targets Python 3.8+.
- **not_yanked** (0.10): latest version is not yanked.
- **release_cadence** (0.20): has had a release in the past 2 years.
- **download_trend** (0.15): last_month downloads > 0 (requires pypistats data).
- **github_active** (0.10): last GitHub push within 2 years (requires GitHub data).

The total of the weights above is 1.0.  Missing optional data (pypistats,
GitHub) simply contributes 0 to those components; the score is still
normalised to [0, 1] based on the max achievable given available data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pypi_librarian.github import GitHubInfo
    from pypi_librarian.models import ProjectInfo
    from pypi_librarian.pypistats import DownloadStats

__all__ = ["HealthScore", "score_project"]

# ISO 8601 date prefix, e.g. "2024-01-15T10:00:00"
_ISO_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")
# Minimum Python version string that we consider "recent"
_RECENT_PY_RE = re.compile(r">=\s*3\.(\d+)")
_RECENT_PY_MINOR_THRESHOLD = 8  # 3.8+

_TWO_YEARS_DAYS = 730


@dataclass
class HealthScore:
    """Result of a health/activity score computation."""

    score: float  # 0.0 – 1.0
    # Per-component results for transparency
    components: dict[str, float] = field(default_factory=dict)
    # Human-readable notes about what drove the score
    notes: list[str] = field(default_factory=list)


def score_project(
    info: "ProjectInfo",
    releases_upload_times: list[str] | None = None,
    stats: "DownloadStats | None" = None,
    github: "GitHubInfo | None" = None,
) -> HealthScore:
    """
    Compute a health score for a project.

    Args:
        info: :class:`~pypi_librarian.models.ProjectInfo` for the latest version.
        releases_upload_times: List of ``upload_time`` strings from
            :class:`~pypi_librarian.models.ReleaseFile` objects, used to
            assess release cadence.  Pass ``None`` to skip.
        stats: Optional :class:`~pypi_librarian.pypistats.DownloadStats`.
        github: Optional :class:`~pypi_librarian.github.GitHubInfo`.

    Returns:
        A :class:`HealthScore` with a ``score`` in [0.0, 1.0] and per-component
        breakdown in ``components``.
    """
    weights: dict[str, float] = {
        "has_summary": 0.10,
        "has_classifiers": 0.10,
        "has_license": 0.10,
        "requires_python_recent": 0.15,
        "not_yanked": 0.10,
        "release_cadence": 0.20,
        "download_trend": 0.15,
        "github_active": 0.10,
    }

    earned: dict[str, float] = {}
    notes: list[str] = []

    # --- has_summary ---
    if info.summary and info.summary.strip():
        earned["has_summary"] = weights["has_summary"]
    else:
        earned["has_summary"] = 0.0
        notes.append("No package summary")

    # --- has_classifiers ---
    if info.classifiers:
        earned["has_classifiers"] = weights["has_classifiers"]
    else:
        earned["has_classifiers"] = 0.0
        notes.append("No PyPI classifiers")

    # --- has_license ---
    if info.license and info.license.strip():
        earned["has_license"] = weights["has_license"]
    else:
        earned["has_license"] = 0.0
        notes.append("No license declared")

    # --- requires_python_recent ---
    rp = info.requires_python or ""
    m = _RECENT_PY_RE.search(rp)
    if m and int(m.group(1)) >= _RECENT_PY_MINOR_THRESHOLD:
        earned["requires_python_recent"] = weights["requires_python_recent"]
    else:
        earned["requires_python_recent"] = 0.0
        if not rp:
            notes.append("No requires_python specified")
        else:
            notes.append(f"requires_python ({rp}) targets older Python")

    # --- not_yanked ---
    if not info.yanked:
        earned["not_yanked"] = weights["not_yanked"]
    else:
        earned["not_yanked"] = 0.0
        notes.append("Latest version is yanked")

    # --- release_cadence ---
    if releases_upload_times:
        recent = _any_within_days(releases_upload_times, _TWO_YEARS_DAYS)
        if recent:
            earned["release_cadence"] = weights["release_cadence"]
        else:
            earned["release_cadence"] = 0.0
            notes.append("No release in the past 2 years")
    else:
        # No data — treat as neutral; exclude from max achievable
        earned["release_cadence"] = 0.0

    # --- download_trend ---
    if stats is not None:
        if stats.last_month > 0:
            earned["download_trend"] = weights["download_trend"]
        else:
            earned["download_trend"] = 0.0
            notes.append("Zero downloads last month (pypistats)")
    else:
        earned["download_trend"] = 0.0  # not measured

    # --- github_active ---
    if github is not None:
        if github.last_push and _within_days(github.last_push, _TWO_YEARS_DAYS):
            earned["github_active"] = weights["github_active"]
        else:
            earned["github_active"] = 0.0
            notes.append("GitHub repo has not been pushed to in 2+ years")
    else:
        earned["github_active"] = 0.0  # not measured

    # Normalise: only count weights for components where we had data
    max_achievable = (
        weights["has_summary"]
        + weights["has_classifiers"]
        + weights["has_license"]
        + weights["requires_python_recent"]
        + weights["not_yanked"]
        + (weights["release_cadence"] if releases_upload_times is not None else 0.0)
        + (weights["download_trend"] if stats is not None else 0.0)
        + (weights["github_active"] if github is not None else 0.0)
    )

    total_earned = sum(earned.values())
    score = round(total_earned / max_achievable, 4) if max_achievable > 0 else 0.0

    return HealthScore(score=score, components=earned, notes=notes)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_date(ts: str) -> datetime | None:
    """Parse the first YYYY-MM-DD from an ISO 8601 string.  Returns None on failure."""
    m = _ISO_PREFIX.match(ts)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _within_days(ts: str, days: int) -> bool:
    dt = _parse_date(ts)
    if dt is None:
        return False
    age = (datetime.now(timezone.utc) - dt).days
    return age <= days


def _any_within_days(timestamps: list[str], days: int) -> bool:
    return any(_within_days(ts, days) for ts in timestamps if ts)
