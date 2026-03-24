# coding=utf-8
"""
Integration test for FetchMetadata bulk download.

Requires:
- Live network access to PyPI.
- A locally cached ``packages.html`` file at
  ``pypi_librarian/packages.html`` (obtained by saving
  https://pypi.org/simple/ to that path).

The test is skipped automatically if the required file is absent.
"""

from __future__ import annotations

import os
import time

import pytest

from pypi_librarian.fetch_metadata import FetchMetadata
from pypi_librarian.json_endpoints import JsonEndpoints

_PACKAGES_HTML = os.path.join(
    os.path.dirname(__file__), "..", "pypi_librarian", "packages.html"
)


@pytest.mark.integration
@pytest.mark.skipif(
    not os.path.exists(_PACKAGES_HTML),
    reason="packages.html cache file not present — save https://pypi.org/simple/ to pypi_librarian/packages.html to enable this test",
)
def test_download_anyone():
    t0 = time.time()

    def go():
        je = JsonEndpoints()
        fetcher = FetchMetadata("tmp", je.package_json_as_text, 2)
        fetcher.generate_packages()

    go()
    t1 = time.time()
    print(f"Elapsed: {t1 - t0:.2f}s")
