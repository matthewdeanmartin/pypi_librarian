# coding=utf-8
"""
Unit tests for models.py — no network access required.
"""

from __future__ import annotations

import pytest

from pypi_librarian.models import (
    Package,
    Project,
    ProjectInfo,
    Release,
    ReleaseFile,
    User,
    _package_from_json,
    _project_from_json,
    _project_info_from_dict,
    _release_file_from_dict,
    _release_from_version_entry,
    _user_from_html,
)


# ---------------------------------------------------------------------------
# ReleaseFile
# ---------------------------------------------------------------------------


def test_release_file_from_dict(sample_release_file_dict):
    rf = _release_file_from_dict(sample_release_file_dict)
    assert rf.filename == "test_pkg-1.0.0-py3-none-any.whl"
    assert rf.sha256_digest == "def456abc789"
    assert rf.md5_digest == "abc123"
    assert rf.packagetype == "bdist_wheel"
    assert rf.yanked is False
    assert rf.yanked_reason is None
    assert rf.requires_python == ">=3.10"


def test_release_file_optional_fields_have_defaults():
    minimal = {
        "filename": "pkg-1.0.tar.gz",
        "url": "https://example.com/pkg-1.0.tar.gz",
        "digests": {"sha256": "abc", "md5": "def"},
        "packagetype": "sdist",
        "python_version": "source",
        "upload_time": "2024-01-01T00:00:00",
    }
    rf = _release_file_from_dict(minimal)
    assert rf.requires_python is None
    assert rf.yanked is False
    assert rf.yanked_reason is None
    assert rf.size == 0


def test_release_file_is_frozen(sample_release_file_dict):
    rf = _release_file_from_dict(sample_release_file_dict)
    with pytest.raises((AttributeError, TypeError)):
        rf.filename = "changed"  # type: ignore[misc]


def test_release_file_raw_is_original_dict(sample_release_file_dict):
    rf = _release_file_from_dict(sample_release_file_dict)
    assert rf.raw is sample_release_file_dict


# ---------------------------------------------------------------------------
# ProjectInfo
# ---------------------------------------------------------------------------


def test_project_info_from_dict_full(sample_info_dict):
    info = _project_info_from_dict(sample_info_dict)
    assert info.name == "test-pkg"
    assert info.version == "1.0.0"
    assert info.summary == "A test package"
    assert info.author_email == "test@example.com"
    assert info.license == "MIT"
    assert info.requires_python == ">=3.10"
    assert info.project_url == "https://example.com"
    assert "License :: OSI Approved :: MIT License" in info.classifiers
    assert "requests>=2.0" in info.requires_dist


def test_project_info_from_dict_minimal():
    info = _project_info_from_dict({"name": "minimal", "version": "0.1"})
    assert info.name == "minimal"
    assert info.summary is None
    assert info.author is None
    assert info.classifiers == ()
    assert info.requires_dist == ()
    assert info.yanked is False


def test_project_info_project_url_fallback():
    """project_url falls back to home_page when project_urls is absent."""
    info = _project_info_from_dict({
        "name": "x",
        "version": "1",
        "home_page": "https://fallback.example.com",
    })
    assert info.project_url == "https://fallback.example.com"


def test_project_info_classifiers_and_requires_dist_are_tuples(sample_info_dict):
    info = _project_info_from_dict(sample_info_dict)
    assert isinstance(info.classifiers, tuple)
    assert isinstance(info.requires_dist, tuple)


def test_project_info_is_frozen(sample_info_dict):
    info = _project_info_from_dict(sample_info_dict)
    with pytest.raises((AttributeError, TypeError)):
        info.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------


def test_release_from_version_entry_with_files(sample_release_file_dict):
    release = _release_from_version_entry("1.0.0", [sample_release_file_dict])
    assert release.version == "1.0.0"
    assert len(release.files) == 1
    assert isinstance(release.files[0], ReleaseFile)


def test_release_from_version_entry_empty():
    release = _release_from_version_entry("0.9.0", [])
    assert release.version == "0.9.0"
    assert release.files == []


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


def test_project_from_json(sample_project_json):
    project = _project_from_json(sample_project_json)
    assert isinstance(project, Project)
    assert project.name == "test-pkg"
    assert isinstance(project.info, ProjectInfo)
    assert len(project.releases) == 2
    assert len(project.latest_files) == 1


def test_project_releases_include_empty_versions(sample_project_json):
    project = _project_from_json(sample_project_json)
    versions = [r.version for r in project.releases]
    assert "0.9.0" in versions
    assert "1.0.0" in versions


def test_project_raw_is_original(sample_project_json):
    project = _project_from_json(sample_project_json)
    assert project.raw is sample_project_json


# ---------------------------------------------------------------------------
# Package
# ---------------------------------------------------------------------------


def test_package_from_json(sample_project_json):
    pkg = _package_from_json(sample_project_json)
    assert isinstance(pkg, Package)
    assert pkg.name == "test-pkg"
    assert pkg.version == "1.0.0"
    assert isinstance(pkg.info, ProjectInfo)
    assert len(pkg.files) == 1


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


def test_user_from_html(sample_user_html):
    user = _user_from_html("testuser", sample_user_html)
    assert isinstance(user, User)
    assert user.name == "testuser"
    assert "alpha" in user.packages
    assert "beta" in user.packages


def test_user_from_html_deduplicates(sample_user_html):
    user = _user_from_html("testuser", sample_user_html)
    assert user.packages.count("alpha") == 1


def test_user_from_html_excludes_non_project_links(sample_user_html):
    user = _user_from_html("testuser", sample_user_html)
    assert "about" not in user.packages
    assert "About" not in user.packages


def test_user_from_html_empty_page():
    user = _user_from_html("nobody", "<html><body>No packages</body></html>")
    assert user.packages == []
