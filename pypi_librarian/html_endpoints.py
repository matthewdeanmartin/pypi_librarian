# coding=utf-8
"""
Parsing data available via HTML

List of all packages in one huge HTML doc.
GET /simple/

"""
from typing import List
from lxml import html
import requests


class HtmlEndpoints(object):
    """
    HTML scraping of pypi.org website
    """

    def __init__(self) -> None:
        pass

    def project_page(self, name: str) -> str:
        """
        Fetch text of page
        :param name:
        :return:
        """
        response = requests.get("https://pypi.org/project/{0}/".format(name))
        return response.text

    def user_page(self, name: str) -> str:
        """
        Fetch text of page
        :param name:
        :return:
        """
        response = requests.get("https://pypi.org/user/{0}/".format(name))
        return response.text

    def all(self) -> List[str]:
        """
        Fetch list of all packages. This is an actual recommended API endpoint
        :param name:
        :return:
        """
        response = requests.get("https://pypi.org/simple/")

        tree = html.fromstring(response.content)

        package_list = [package for package in tree.xpath("//a/text()")]
        return package_list


if __name__ == "__main__":

    def run() -> None:
        """
        Exercise code
        :return:
        """
        hep = HtmlEndpoints()
        page = hep.project_page("requests")
        # print(page)
        for row in page.split("\n"):
            if "user" in row:
                print(row)
        user = hep.user_page("matthewdeanmartin")
        print(user)

    run()
