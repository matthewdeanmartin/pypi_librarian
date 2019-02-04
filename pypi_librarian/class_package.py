# coding=utf-8
"""
A single release
"""
from pypi_librarian.json_endpoints import JsonEndpoints


class Package(object):
    """
    Properties and state for Package
    """

    def __init__(self, name: str, version: str) -> None:
        """
        Initialize values
        :param name:
        :param version:
        """
        self.name = name
        self.version = version
        je = JsonEndpoints()
        self.metadata = je.package_json(self.name)
        self.normalized_name = self.metadata["info"]["name"]
        self.owner = self.metadata["info"]["author_email"]

    def stats(self) -> None:
        return None
