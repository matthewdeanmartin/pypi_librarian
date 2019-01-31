# coding=utf-8
"""
Data and actions representing a repo, which usually is just pypi. Could also be some mirror or other pypi compatible repo.
"""
from typing import List

from pypi_librarian.class_package import Package
from pypi_librarian.class_project import Project
from pypi_librarian.class_user import User


class Repository(object):
    """
    Properties and methods
    """

    def __init__(self, default: bool = True) -> None:
        """
        Initialize values
        :param default:
        """
        self.url = "https://pypi.org"

    def get_current_package(self, name: str) -> Package:
        """
        Short cut to get current package from Package object
        :param name:
        :return:
        """
        project = Project(name)
        return project.current_package()

    def get_project(self, name: str) -> Project:
        """
        Accesss to package object
        :param name:
        :return:
        """
        if not name:
            raise TypeError("Package Name required")
        project = Project(name)
        return project

    def get_user(self, name: str) -> User:
        """
        Access to user object
        :param name:
        :return:
        """
        if not name:
            raise TypeError("User Name required")
        user = User(name)
        return user

    def projects_by_user(self, name: str) -> List[Project]:
        """
        List of projects by user.
        :param name:
        :return:
        """
        if not name:
            raise TypeError("User Name required")
        return []

    def search_projects(self, query: str) -> List[Project]:
        """
        Attempt to search for a project
        :param query:
        :return:
        """
        if not query:
            raise TypeError("Query required")
        return []
