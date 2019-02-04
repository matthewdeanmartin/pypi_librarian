# coding=utf-8
"""
Just exercise code
"""
import time

from pypi_librarian.fetch_metadata import FetchMetadata
from pypi_librarian.json_endpoints import JsonEndpoints


def test_download_anyone():
    t0 = time.time()

    def go():
        je = JsonEndpoints()
        fetcher = FetchMetadata("tmp", je.package_json_as_text, 2)
        fetcher.generate_packages()


    go()
    t1 = time.time()

    total = t1 - t0
    print(total)