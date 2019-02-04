# coding=utf-8
"""
Test all kinds of endpoints in one place
"""
from pypi_librarian.html_endpoints import HtmlEndpoints
from pypi_librarian.json_endpoints import JsonEndpoints
from pypi_librarian.rss_endpoints import RssEndpoints
import pypi_xmlrpc

def test_html():
    hep = HtmlEndpoints()
    page = hep.project_page("requests")
    # print(page)
    for row in page.split("\n"):
        if "user" in row:
            print(row)
    user = hep.user_page("matthewdeanmartin")
    print(user)


def test_json():
    je = JsonEndpoints()
    print(je.package_json("jiggle_version"))
    print(je.package_version_json("jiggle_version", "1.0.68"))

def test_rss():
    client = RssEndpoints()
    print(client.latest_packages())
    print(client.newest_packages())

def test_xmlrpc():
    # TODO: This doesn't test *my* code.
    name = "jiggle_version"
    user = "matthewdeanmartin"
    version = "1.0.68"
    # x = pypi_xmlrpc.list_packages()	# return list of all server packages
    # print(x)
    x = pypi_xmlrpc.package_releases(
        name, show_hidden=True
    )  # return list of package releases
    print(x)
    x = pypi_xmlrpc.package_roles(name)  # return list of package roles
    print(x)
    x = pypi_xmlrpc.release_data(
        name, version
    )  # return dictionary with release data
    print(x)
    x = pypi_xmlrpc.release_urls(name, version)  # return list of release urls
    print(x)
    x = pypi_xmlrpc.user_packages(user)  # return list of user packages
    print(x)