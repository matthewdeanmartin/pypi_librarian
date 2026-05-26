# coding=utf-8
"""
Tests for Repository — the primary entry point.

Unit tests mock HTTP; integration tests hit live PyPI and require network.
Run only unit tests with:  pytest -m "not integration"
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pypi_librarian.class_repo import Repository
from pypi_librarian.models import NewPackage, NewRelease, Package, Project, User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_json_response(data: dict | None, status: int = 200):
    """Return a mock requests.Response-like object."""
    import json

    mock = MagicMock()
    mock.status_code = status
    mock.text = json.dumps(data) if data is not None else ""
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestGetProject:
    def test_returns_project(self, sample_project_json):
        repo = Repository()
        with patch.object(repo._json, "package_json", return_value=sample_project_json):
            project = repo.get_project("test-pkg")
        assert isinstance(project, Project)
        assert project.name == "test-pkg"

    def test_raises_on_not_found(self):
        repo = Repository()
        with patch.object(repo._json, "package_json", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                repo.get_project("no-such-package")

    def test_raises_on_empty_name(self):
        with pytest.raises(TypeError):
            Repository().get_project("")

    def test_project_has_releases(self, sample_project_json):
        repo = Repository()
        with patch.object(repo._json, "package_json", return_value=sample_project_json):
            project = repo.get_project("test-pkg")
        assert len(project.releases) == 2

    def test_project_has_latest_files(self, sample_project_json):
        repo = Repository()
        with patch.object(repo._json, "package_json", return_value=sample_project_json):
            project = repo.get_project("test-pkg")
        assert len(project.latest_files) == 1


class TestGetPackage:
    def test_returns_package(self, sample_project_json):
        repo = Repository()
        with patch.object(
            repo._json, "package_version_json", return_value=sample_project_json
        ):
            pkg = repo.get_package("test-pkg", "1.0.0")
        assert isinstance(pkg, Package)
        assert pkg.name == "test-pkg"
        assert pkg.version == "1.0.0"

    def test_raises_on_not_found(self):
        repo = Repository()
        with patch.object(repo._json, "package_version_json", return_value=None):
            with pytest.raises(ValueError, match="not found"):
                repo.get_package("test-pkg", "0.0.0")

    def test_raises_on_empty_name(self):
        with pytest.raises(TypeError):
            Repository().get_package("", "1.0.0")

    def test_raises_on_empty_version(self):
        with pytest.raises(TypeError):
            Repository().get_package("test-pkg", "")


class TestGetUser:
    def test_returns_user(self):
        repo = Repository()
        with patch.object(
            repo._html, "packages_for_user", return_value=["alpha", "beta"]
        ):
            user = repo.get_user("testuser")
        assert isinstance(user, User)
        assert user.name == "testuser"
        assert "alpha" in user.packages
        assert "beta" in user.packages

    def test_raises_on_empty_name(self):
        with pytest.raises(TypeError):
            Repository().get_user("")


class TestProjectNamesByUser:
    def test_returns_list_of_strings(self):
        repo = Repository()
        with patch.object(
            repo._html, "packages_for_user", return_value=["alpha", "beta"]
        ):
            names = repo.project_names_by_user("testuser")
        assert names == ["alpha", "beta"]

    def test_raises_on_empty_name(self):
        with pytest.raises(TypeError):
            Repository().project_names_by_user("")


class TestFeedMethods:
    def test_newest_packages_returns_list(self, sample_rss_packages_xml):
        repo = Repository()
        with patch.object(repo._rss, "_fetch", return_value=sample_rss_packages_xml):
            result = repo.newest_packages()
        assert isinstance(result, list)
        assert all(isinstance(p, NewPackage) for p in result)

    def test_newest_packages_count_limit(self, sample_rss_packages_xml):
        repo = Repository()
        with patch.object(repo._rss, "_fetch", return_value=sample_rss_packages_xml):
            result = repo.newest_packages(count=1)
        assert len(result) == 1

    def test_latest_updates_returns_list(self, sample_rss_updates_xml):
        repo = Repository()
        with patch.object(repo._rss, "_fetch", return_value=sample_rss_updates_xml):
            result = repo.latest_updates()
        assert isinstance(result, list)
        assert all(isinstance(r, NewRelease) for r in result)


class TestSearchProjects:
    def test_raises_not_implemented(self):
        with pytest.raises(NotImplementedError, match="search"):
            Repository().search_projects("requests")


# ---------------------------------------------------------------------------
# Integration tests — require live network access to PyPI
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_project_requests_live():
    repo = Repository()
    project = repo.get_project("requests")
    assert project.name == "requests"
    assert project.info.version
    assert len(project.releases) > 0


@pytest.mark.integration
def test_get_package_specific_version_live():
    repo = Repository()
    pkg = repo.get_package("requests", "2.28.0")
    assert pkg.name == "requests"
    assert pkg.version == "2.28.0"
    assert len(pkg.files) > 0


@pytest.mark.integration
def test_get_user_live():
    repo = Repository()
    user = repo.get_user("matthewdeanmartin")
    assert user.name == "matthewdeanmartin"
    assert len(user.packages) > 0


@pytest.mark.integration
def test_get_all_package_names_yields_strings_live():
    repo = Repository()
    names = list(name for name, _ in zip(repo.get_all_package_names(), range(5)))
    assert len(names) == 5
    assert all(isinstance(n, str) for n in names)


@pytest.mark.integration
def test_newest_packages_live():
    repo = Repository()
    packages = repo.newest_packages()
    assert len(packages) > 0
    assert packages[0].title
    assert packages[0].link


@pytest.mark.integration
def test_latest_updates_live():
    repo = Repository()
    updates = repo.latest_updates()
    assert len(updates) > 0
    assert updates[0].title
