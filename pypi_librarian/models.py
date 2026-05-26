# coding=utf-8
"""
Typed dataclass models for PyPI API responses.

Strong models for stable fields + raw: dict passthrough for future PyPI fields.
Factory functions (_x_from_y) construct models from raw API dicts and are private
to this package — callers should use Repository methods instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "NewPackage",
    "NewRelease",
    "Package",
    "Project",
    "ProjectInfo",
    "Release",
    "ReleaseFile",
    "User",
]


# ---------------------------------------------------------------------------
# Leaf value objects (frozen — immutable, hashable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReleaseFile:
    """A single distribution file (wheel, sdist, etc.) for one release."""

    filename: str
    url: str
    size: int
    md5_digest: str
    sha256_digest: str
    packagetype: str  # "bdist_wheel" | "sdist"
    python_version: str  # "py3" | "source" | "cp311" …
    requires_python: str | None
    upload_time: str  # ISO 8601 string
    yanked: bool
    yanked_reason: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectInfo:
    """Top-level metadata from the ``info`` block of the PyPI JSON API."""

    name: str
    version: str
    summary: str | None
    author: str | None
    author_email: str | None
    maintainer: str | None
    maintainer_email: str | None
    license: str | None
    home_page: str | None
    project_url: str | None
    requires_python: str | None
    classifiers: tuple[str, ...]  # tuple so frozen=True works
    keywords: str | None
    description: str | None
    description_content_type: str | None
    requires_dist: tuple[str, ...]
    yanked: bool
    yanked_reason: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NewPackage:
    """An item from the PyPI ``/rss/packages.xml`` (newest packages) feed."""

    title: str
    link: str
    description: str
    published: str  # RFC 2822 date string as-is
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NewRelease:
    """An item from the PyPI ``/rss/updates.xml`` (latest updates) feed."""

    title: str
    link: str
    description: str
    published: str  # RFC 2822 date string as-is
    raw: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Composite models (not frozen — contain list fields)
# ---------------------------------------------------------------------------


@dataclass
class Release:
    """One version of a project with all its distribution files."""

    version: str
    files: list[ReleaseFile]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Package:
    """A specific (name, version) pair with full metadata and file list."""

    name: str
    version: str
    info: ProjectInfo
    files: list[ReleaseFile]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    """All known data about a project across every version."""

    name: str
    info: ProjectInfo  # metadata from the latest version
    releases: list[Release]  # all versions in PyPI order
    latest_files: list[ReleaseFile]  # files for the latest version (``urls`` key)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class User:
    """A PyPI user and the list of packages they maintain."""

    name: str
    packages: list[str]  # package names (not Package objects — avoids N HTTP calls)
    raw: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Private factory functions — construct models from raw API dicts.
# These are the only place that maps PyPI JSON keys to model fields.
# ---------------------------------------------------------------------------


def _release_file_from_dict(d: dict[str, Any]) -> ReleaseFile:
    digests = d.get("digests") or {}
    return ReleaseFile(
        filename=d["filename"],
        url=d["url"],
        size=d.get("size", 0),
        md5_digest=digests.get("md5", ""),
        sha256_digest=digests.get("sha256", ""),
        packagetype=d.get("packagetype", ""),
        python_version=d.get("python_version", ""),
        requires_python=d.get("requires_python"),
        upload_time=d.get("upload_time", ""),
        yanked=d.get("yanked", False),
        yanked_reason=d.get("yanked_reason"),
        raw=d,
    )


def _project_info_from_dict(info: dict[str, Any]) -> ProjectInfo:
    project_urls: dict[str, str] = info.get("project_urls") or {}
    project_url = (
        project_urls.get("Homepage")
        or project_urls.get("homepage")
        or info.get("home_page")
    )
    return ProjectInfo(
        name=info.get("name", ""),
        version=info.get("version", ""),
        summary=info.get("summary"),
        author=info.get("author"),
        author_email=info.get("author_email"),
        maintainer=info.get("maintainer"),
        maintainer_email=info.get("maintainer_email"),
        license=info.get("license"),
        home_page=info.get("home_page"),
        project_url=project_url,
        requires_python=info.get("requires_python"),
        classifiers=tuple(info.get("classifiers") or []),
        keywords=info.get("keywords"),
        description=info.get("description"),
        description_content_type=info.get("description_content_type"),
        requires_dist=tuple(info.get("requires_dist") or []),
        yanked=info.get("yanked", False),
        yanked_reason=info.get("yanked_reason"),
        raw=info,
    )


def _release_from_version_entry(
    version: str, file_list: list[dict[str, Any]]
) -> Release:
    return Release(
        version=version,
        files=[_release_file_from_dict(f) for f in file_list],
        raw={"version": version, "files": file_list},
    )


def _project_from_json(data: dict[str, Any]) -> Project:
    info = _project_info_from_dict(data["info"])
    releases_raw: dict[str, list[dict[str, Any]]] = data.get("releases") or {}
    releases = [
        _release_from_version_entry(ver, files) for ver, files in releases_raw.items()
    ]
    latest_files = [_release_file_from_dict(f) for f in (data.get("urls") or [])]
    return Project(
        name=info.name,
        info=info,
        releases=releases,
        latest_files=latest_files,
        raw=data,
    )


def _package_from_json(data: dict[str, Any]) -> Package:
    info = _project_info_from_dict(data["info"])
    files = [_release_file_from_dict(f) for f in (data.get("urls") or [])]
    return Package(
        name=info.name,
        version=info.version,
        info=info,
        files=files,
        raw=data,
    )


def _user_from_html(name: str, html_text: str) -> User:
    """Parse a PyPI user profile page to extract maintained package names."""
    from lxml import html as lxml_html  # local import — lxml only needed here

    tree = lxml_html.fromstring(html_text)
    hrefs: list[str] = tree.xpath("//a[contains(@href, '/project/')]/@href")
    seen: set[str] = set()
    packages: list[str] = []
    for href in hrefs:
        # href looks like "/project/some-package/"
        slug = href.strip("/").split("/")[-1]
        if slug and slug not in seen:
            seen.add(slug)
            packages.append(slug)
    return User(name=name, packages=packages, raw={"html_parsed": True})


def _new_package_from_rss_item(item: Any) -> NewPackage:
    """Build a NewPackage from an xml.etree.ElementTree ``<item>`` element."""
    return NewPackage(
        title=_rss_text(item, "title"),
        link=_rss_text(item, "link"),
        description=_rss_text(item, "description"),
        published=_rss_text(item, "pubDate"),
        raw={child.tag: child.text for child in item},
    )


def _new_release_from_rss_item(item: Any) -> NewRelease:
    """Build a NewRelease from an xml.etree.ElementTree ``<item>`` element."""
    return NewRelease(
        title=_rss_text(item, "title"),
        link=_rss_text(item, "link"),
        description=_rss_text(item, "description"),
        published=_rss_text(item, "pubDate"),
        raw={child.tag: child.text for child in item},
    )


def _rss_text(item: Any, tag: str) -> str:
    el = item.find(tag)
    return (el.text or "").strip() if el is not None else ""
