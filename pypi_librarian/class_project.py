# coding=utf-8
"""
A collection of versioned packages, ie. releases.
"""
from typing import List

import pypi_xmlrpc

from pypi_librarian.class_package import Package
from pypi_librarian.json_endpoints import JsonEndpoints


class Project(object):
    """
    Properties and methods
    """

    def __init__(self, name) -> None:
        """
        Initialize values
        :param name:
        """
        self.name = name
        self.normalized_name = ""
        je = JsonEndpoints()
        data = je.package_json(self.name)

        if data is None:
            raise TypeError("That package doesn't exist on the repository")

        self.main_package_json = data
        # different schema from json.
        self.xml_rpc_info = pypi_xmlrpc.release_data(
            self.name, self.main_package_json["info"]["version"]
        )
        package = Package(self.name, self.main_package_json["info"]["version"])
        self.main_package = package

    def current_package(self) -> Package:
        """
        Get package object for most recent version
        :return:
        """
        # seems like anyone will do
        # url = data["urls"][0]["url"]
        # version = None
        # for key in data["releases"].keys():
        #     if key in url:
        #         version = key
        # if not version:
        #     raise TypeError("No current version of this project.")
        return self.main_package

    def all_releases(self, package: Package) -> List[Package]:
        """
        Get package object for each version or release that exists
        :param package:
        :return:
        """
        releases = []
        for version, release_info in self.main_package_json["releases"].items(0):
            package = Package(self.name, version)
            releases.append(package)
        return releases
