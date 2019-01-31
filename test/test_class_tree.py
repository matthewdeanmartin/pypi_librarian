# coding=utf-8
"""
Exercise class heirarchy
"""
from typing import List, Dict
from pypi_librarian.class_repo import Repository
from pypi_librarian.class_project import Project
from pypi_librarian.class_package import Package
from pypi_librarian.class_user import User


def test_all() -> None:
    repo = Repository()
    name = "jiggle_version"

    project = repo.get_project(name)
    current_package = project.current_package()
    user_name = current_package.owner
    user_info = repo.get_user(user_name)
    names = user_info.get_packages_name()
