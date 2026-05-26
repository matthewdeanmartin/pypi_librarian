# coding=utf-8
"""
Download statistics from pypistats.org.

Fetches from ``https://pypistats.org/api/packages/{name}/recent``.
Returns a :class:`DownloadStats` dataclass with last-day, last-week,
and last-month counts.

The stats endpoint is public and does not require authentication, but
results are cached aggressively on the server side (updated daily).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

__all__ = ["DownloadStats", "fetch_download_stats"]

_BASE = "https://pypistats.org/api"


@dataclass(frozen=True)
class DownloadStats:
    """Download counts for a package from pypistats.org."""

    package: str
    last_day: int
    last_week: int
    last_month: int
    raw: dict[str, Any] = field(default_factory=dict)


def fetch_download_stats(
    name: str,
    *,
    client: httpx.Client | None = None,
) -> DownloadStats | None:
    """
    Fetch download stats for *name* from pypistats.org.

    Returns ``None`` if the package is unknown to pypistats (404).
    Raises ``httpx.HTTPStatusError`` on other HTTP errors.

    Args:
        name: PyPI package name.
        client: Optional ``httpx.Client`` to reuse.  A temporary client is
            created and closed if not provided.
    """
    url = f"{_BASE}/packages/{name}/recent"
    _own_client = client is None
    if _own_client:
        client = httpx.Client(timeout=30.0)
    assert client is not None
    try:
        response = client.get(url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data: dict[str, Any] = json.loads(response.text)
    finally:
        if _own_client:
            client.close()

    rows: list[dict[str, Any]] = data.get("data", [])
    counts: dict[str, int] = {}
    for row in rows:
        category = row.get("category", "")
        downloads = int(row.get("downloads", 0))
        counts[category] = downloads

    return DownloadStats(
        package=name,
        last_day=counts.get("last_day", 0),
        last_week=counts.get("last_week", 0),
        last_month=counts.get("last_month", 0),
        raw=data,
    )
