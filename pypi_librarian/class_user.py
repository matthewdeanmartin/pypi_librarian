# coding=utf-8
"""
Data and actions for user
"""
from typing import List

import pypi_xmlrpc

from pypi_librarian.class_package import Package


class User(object):
    """
    Properties and methods
    """

    def __init__(self, name: str) -> None:
        """
        Initialize values
        :param name:
        """
        self.name = name

    def get_packages_name(self) -> List[str]:
        """
        xmlprc call to get user info, but just names
        :return:
        """
        packages = pypi_xmlrpc.user_packages(self.name)
        return packages

    def get_packages(self, name: str, version: str) -> List[Package]:
        """
        Load all packages for user, entire package objects
        :param name:
        :param version:
        :return:
        """
        raise NotImplementedError()
