# coding=utf-8
"""
Optional GitHub metadata enrichment.

Extracts a GitHub repository URL from a package's ``ProjectInfo`` and
fetches public repository metadata (stars, open issues, last push date,
default branch).

A GitHub personal-access token can be supplied via the ``GITHUB_TOKEN``
environment variable or the ``token`` argument to avoid rate limiting
(60 unauthenticated req/hr vs 5 000 authenticated).  If the token is
absent the call still succeeds but may be throttled for bulk workloads.

The module gracefully returns ``None`` whenever GitHub enrichment is not
possible (no URL found, 404, rate-limited, network error).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

__all__ = ["GitHubInfo", "fetch_github_info", "extract_github_repo"]

_GITHUB_API = "https://api.github.com"
# Match https://github.com/owner/repo  (with optional .git suffix / trailing slash)
_GITHUB_RE = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+?)(?:\.git)?/?$"
)


@dataclass(frozen=True)
class GitHubInfo:
    """Public repository metadata fetched from the GitHub REST API."""

    owner: str
    repo: str
    stars: int
    forks: int
    open_issues: int
    # ISO 8601 timestamp of the last push, e.g. "2024-03-15T12:00:00Z"
    last_push: str | None
    description: str | None
    archived: bool
    raw: dict[str, Any] = field(default_factory=dict)


def extract_github_repo(project_url: str | None, home_page: str | None) -> tuple[str, str] | None:
    """
    Extract ``(owner, repo)`` from a package's project or home-page URL.

    Returns ``None`` if neither URL points to GitHub.
    """
    for url in (project_url, home_page):
        if not url:
            continue
        m = _GITHUB_RE.match(url.strip())
        if m:
            return m.group(1), m.group(2)
    return None


def fetch_github_info(
    owner: str,
    repo: str,
    *,
    token: str | None = None,
    client: httpx.Client | None = None,
) -> GitHubInfo | None:
    """
    Fetch public repository metadata for *owner*/*repo* from the GitHub API.

    Returns ``None`` if the repository is not found (404) or if the request
    is rate-limited (403/429).  Other HTTP errors are raised.

    Args:
        owner: GitHub user or organisation name.
        repo: Repository name.
        token: GitHub personal-access token.  Falls back to the
            ``GITHUB_TOKEN`` environment variable.  Optional — unauthenticated
            requests are allowed but rate-limited to 60/hr.
        client: Optional ``httpx.Client`` to reuse.
    """
    resolved_token = token or os.environ.get("GITHUB_TOKEN")
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if resolved_token:
        headers["Authorization"] = f"Bearer {resolved_token}"

    url = f"{_GITHUB_API}/repos/{owner}/{repo}"
    _own_client = client is None
    if _own_client:
        client = httpx.Client(timeout=30.0, headers=headers)
    try:
        response = client.get(url, headers=headers)
        if response.status_code in (403, 404, 429):
            return None
        response.raise_for_status()
        data: dict[str, Any] = json.loads(response.text)
    finally:
        if _own_client:
            client.close()

    return GitHubInfo(
        owner=owner,
        repo=repo,
        stars=int(data.get("stargazers_count", 0)),
        forks=int(data.get("forks_count", 0)),
        open_issues=int(data.get("open_issues_count", 0)),
        last_push=data.get("pushed_at"),
        description=data.get("description"),
        archived=bool(data.get("archived", False)),
        raw=data,
    )


def fetch_github_info_for_project(
    project_url: str | None,
    home_page: str | None,
    *,
    token: str | None = None,
    client: httpx.Client | None = None,
) -> GitHubInfo | None:
    """
    Convenience wrapper: extract the GitHub repo URL from project metadata
    and fetch its info.  Returns ``None`` if no GitHub URL is found or if
    the fetch fails gracefully.
    """
    coords = extract_github_repo(project_url, home_page)
    if coords is None:
        return None
    owner, repo = coords
    return fetch_github_info(owner, repo, token=token, client=client)
