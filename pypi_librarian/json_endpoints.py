# coding=utf-8
"""

Package level
GET /pypi/<project_name>/json

Release level
GET /pypi/<project_name>/<version>/json


Top 100 packages
GET /stats/
ref https://github.com/cooperlees/pypistats

(similar named but different service: https://github.com/hugovk/pypistats)

"""
import json
from typing import Any

import requests


class JsonEndpoints(object):
    def __init__(self, repo_url="https://pypi.python.org/pypi") -> None:
        self.s = None
        self.index_url = repo_url

    def get(self, *path) -> requests.Response:
        if self.s is None:
            self.s = requests.Session()
        return self.s.get(self.index_url.rstrip("/") + "/" + "/".join(path))

    def package_json_as_text(self, package: str) -> Any:
        """
        Fetch json, put in dictionary
        :param package:
        :return:
        """
        response = self.get("{0}/json".format(package))
        if response.status_code == 404:
            return None
        else:
            return response.text

    def package_json(self, package: str) -> Any:
        """
        Fetch json, put in dictionary
        :param package:
        :return:
        """
        response = self.get("{0}/json".format(package))
        if response.status_code == 404:
            return None
        else:
            return json.loads(response.text)

    def package_version_json(self, package: str, version: str) -> Any:
        """
        Fetch json and put in dictionary
        :param package:
        :param version:
        :return:
        """
        response = self.get("{0}/{1}/json".format(package, version))
        return json.loads(response.text)


if __name__ == "__main__":

    def run() -> None:
        je = JsonEndpoints()
        print(je.package_json("jiggle_version"))
        print(je.package_version_json("jiggle_version", "1.0.68"))

    run()
