# coding=utf-8
"""
Integration test that exercises the full class hierarchy end-to-end.
Requires live network access to PyPI.
"""

from __future__ import annotations

import pytest

from pypi_librarian.class_repo import Repository
from pypi_librarian.models import Package, Project, User


@pytest.mark.integration
def test_all() -> None:
    repo = Repository()
    name = "jiggle_version"

    # get the project (PyPI normalises underscores to hyphens)
    project = repo.get_project(name)
    assert isinstance(project, Project)
    assert project.name.replace("-", "_") == name

    # inspect latest version info (PyPI normalises underscores to hyphens)
    info = project.info
    assert info.version
    assert info.name.replace("-", "_") == name

    # look up the known maintainer by PyPI username (not author_email, which is
    # a display string like "Name <email>" and is not a PyPI username)
    user_info = repo.get_user("matthewdeanmartin")
    assert isinstance(user_info, User)
    assert len(user_info.packages) > 0


@pytest.mark.integration
def test_get_specific_version() -> None:
    repo = Repository()
    project = repo.get_project("jiggle_version")
    assert len(project.releases) > 0

    # pick the first available version and fetch it specifically
    first_version = project.releases[0].version
    pkg = repo.get_package("jiggle_version", first_version)
    assert isinstance(pkg, Package)
    assert pkg.version == first_version


@pytest.mark.integration
def test_project_names_by_user() -> None:
    repo = Repository()
    names = repo.project_names_by_user("matthewdeanmartin")
    assert isinstance(names, list)
    assert len(names) > 0
    assert all(isinstance(n, str) for n in names)
