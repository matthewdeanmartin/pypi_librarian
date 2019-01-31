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
from typing import Any
import requests
import json


def package_json(package: str) -> Any:
    """
    Fetch json, put in dictionary
    :param package:
    :return:
    """
    response = requests.get("https://pypi.python.org/pypi/{0}/json".format(package))
    return json.loads(response.text)


def package_version_json(package: str, version: str) -> Any:
    """
    Fetch json and put in dictionary
    :param package:
    :param version:
    :return:
    """
    response = requests.get(
        "https://pypi.python.org/pypi/{0}/{1}/json".format(package, version)
    )
    return json.loads(response.text)


if __name__ == "__main__":

    def run() -> None:
        print(package_json("jiggle_version"))
        print(package_version_json("jiggle_version", "1.0.68"))

    run()
