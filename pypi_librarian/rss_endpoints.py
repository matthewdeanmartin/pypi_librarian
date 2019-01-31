# coding=utf-8
"""
Most likely use case: syncing pypi mirrors.

Newest
https://pypi.org/rss/packages.xml

Latest
https://pypi.org/rss/updates.xml,

"""

# get a reall rss library

# wrap pypi's feeds

import requests


class RssEndpoints(object):
    """
    Methods and properties
    """

    def __init__(self) -> None:
        """
        initialized values
        """
        pass

    def newest_packages(self) -> str:
        """
        Fetch raw RSS text
        :return:
        """
        response = requests.get("https://pypi.org/rss/packages.xml")
        return response.text

    def latest_packages(self) -> str:
        """
        Fetch raw RSS text
        :return:
        """
        response = requests.get("https://pypi.org/rss/updates.xml")
        return response.text


if __name__ == "__main__":

    def run() -> None:
        """
        Exercise code
        :return:
        """
        client = RssEndpoints()
        print(client.latest_packages())
        print(client.newest_packages())

    run()
