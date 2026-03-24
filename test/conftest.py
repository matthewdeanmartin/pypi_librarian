# coding=utf-8
"""
Shared pytest fixtures and marker registration.

Integration tests (those that require live network access to PyPI) are
decorated with ``@pytest.mark.integration`` and can be excluded with::

    pytest -m "not integration"
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Fixtures — minimal valid PyPI API payloads for unit tests
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_release_file_dict() -> dict:
    return {
        "filename": "test_pkg-1.0.0-py3-none-any.whl",
        "url": "https://files.pythonhosted.org/packages/test_pkg-1.0.0-py3-none-any.whl",
        "size": 12345,
        "digests": {"md5": "abc123", "sha256": "def456abc789"},
        "packagetype": "bdist_wheel",
        "python_version": "py3",
        "requires_python": ">=3.10",
        "upload_time": "2024-01-01T00:00:00",
        "yanked": False,
        "yanked_reason": None,
    }


@pytest.fixture()
def sample_info_dict() -> dict:
    return {
        "name": "test-pkg",
        "version": "1.0.0",
        "summary": "A test package",
        "author": "Test Author",
        "author_email": "test@example.com",
        "maintainer": None,
        "maintainer_email": None,
        "license": "MIT",
        "home_page": "https://example.com",
        "project_urls": {"Homepage": "https://example.com"},
        "requires_python": ">=3.10",
        "classifiers": ["License :: OSI Approved :: MIT License"],
        "keywords": "test",
        "description": "Long description here.",
        "description_content_type": "text/plain",
        "requires_dist": ["requests>=2.0"],
        "yanked": False,
        "yanked_reason": None,
    }


@pytest.fixture()
def sample_project_json(sample_info_dict, sample_release_file_dict) -> dict:
    return {
        "info": sample_info_dict,
        "releases": {
            "0.9.0": [],  # version with no files
            "1.0.0": [sample_release_file_dict],
        },
        "urls": [sample_release_file_dict],
    }


@pytest.fixture()
def sample_rss_packages_xml() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>PyPI newest packages</title>
    <item>
      <title>mypackage 1.0.0</title>
      <link>https://pypi.org/project/mypackage/</link>
      <description>A shiny new package</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
      <guid>https://pypi.org/project/mypackage/</guid>
    </item>
    <item>
      <title>otherpackage 2.3.1</title>
      <link>https://pypi.org/project/otherpackage/</link>
      <description>Another package</description>
      <pubDate>Tue, 02 Jan 2024 08:30:00 GMT</pubDate>
      <guid>https://pypi.org/project/otherpackage/</guid>
    </item>
  </channel>
</rss>"""


@pytest.fixture()
def sample_rss_updates_xml() -> str:
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>PyPI latest updates</title>
    <item>
      <title>requests 2.32.0</title>
      <link>https://pypi.org/project/requests/2.32.0/</link>
      <description>HTTP for Humans</description>
      <pubDate>Wed, 03 Jan 2024 10:00:00 GMT</pubDate>
      <guid>https://pypi.org/project/requests/2.32.0/</guid>
    </item>
  </channel>
</rss>"""


@pytest.fixture()
def sample_user_html() -> str:
    """Minimal PyPI user profile page HTML with two project links."""
    return """\
<html>
<body>
  <a href="/project/alpha/">alpha</a>
  <a href="/project/beta/">beta</a>
  <a href="/project/alpha/">alpha (duplicate)</a>
  <a href="/about/">About</a>
</body>
</html>"""
