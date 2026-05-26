# coding=utf-8
"""
Tests for the bulk CLI commands (download, download-many, fetch-metadata).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pypi_librarian.__main__ import main
from pypi_librarian.download import DownloadResult

# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------


class TestCLIDownload:
    def test_download_success(self, tmp_path):
        result = DownloadResult(
            name="requests",
            version="2.31.0",
            files=[str(tmp_path / "requests-2.31.0-py3-none-any.whl")],
        )
        with patch("pypi_librarian.__main__.Downloader") as MockDL:
            MockDL.return_value.download_one_sync.return_value = result
            exit_code = main(["download", "requests", "--dest", str(tmp_path)])
        assert exit_code == 0

    def test_download_with_version(self, tmp_path):
        result = DownloadResult(
            name="requests",
            version="2.28.0",
            files=[str(tmp_path / "requests-2.28.0-py3-none-any.whl")],
        )
        with patch("pypi_librarian.__main__.Downloader") as MockDL:
            MockDL.return_value.download_one_sync.return_value = result
            exit_code = main(
                ["download", "requests", "-V", "2.28.0", "--dest", str(tmp_path)]
            )
        assert exit_code == 0

    def test_download_with_errors_returns_nonzero(self, tmp_path):
        result = DownloadResult(
            name="bad-pkg",
            version="1.0",
            errors=["connection timeout"],
        )
        with patch("pypi_librarian.__main__.Downloader") as MockDL:
            MockDL.return_value.download_one_sync.return_value = result
            exit_code = main(["download", "bad-pkg", "--dest", str(tmp_path)])
        assert exit_code == 1


# ---------------------------------------------------------------------------
# download-many
# ---------------------------------------------------------------------------


class TestCLIDownloadMany:
    def test_download_many_from_file(self, tmp_path):
        pkg_file = tmp_path / "packages.txt"
        pkg_file.write_text("requests\nflask\n")

        results = [
            DownloadResult(name="requests", version="2.31.0", files=["r.whl"]),
            DownloadResult(name="flask", version="3.0.0", files=["f.whl"]),
        ]
        with patch("pypi_librarian.__main__.Downloader") as MockDL:
            MockDL.return_value.download_many_sync.return_value = results
            exit_code = main(
                ["download-many", "--from-file", str(pkg_file), "--dest", str(tmp_path)]
            )
        assert exit_code == 0

    def test_download_many_file_not_found(self):
        exit_code = main(["download-many", "--from-file", "/nonexistent/file.txt"])
        assert exit_code == 1

    def test_download_many_with_resume(self, tmp_path):
        pkg_file = tmp_path / "packages.txt"
        pkg_file.write_text("requests\n")

        results = [
            DownloadResult(name="requests", version="2.31.0", files=["r.whl"]),
        ]
        with patch("pypi_librarian.__main__.Downloader") as MockDL:
            MockDL.return_value.go_or_resume_sync.return_value = results
            exit_code = main(
                [
                    "download-many",
                    "--from-file",
                    str(pkg_file),
                    "--dest",
                    str(tmp_path),
                    "--resume",
                ]
            )
        assert exit_code == 0
        MockDL.return_value.go_or_resume_sync.assert_called_once()

    def test_download_many_skips_comments_and_blanks(self, tmp_path):
        pkg_file = tmp_path / "packages.txt"
        pkg_file.write_text("# comment\nrequests\n\n# another comment\nflask\n")

        results = [
            DownloadResult(name="requests", version="2.31.0", files=["r.whl"]),
            DownloadResult(name="flask", version="3.0.0", files=["f.whl"]),
        ]
        with patch("pypi_librarian.__main__.Downloader") as MockDL:
            MockDL.return_value.download_many_sync.return_value = results
            exit_code = main(
                ["download-many", "--from-file", str(pkg_file), "--dest", str(tmp_path)]
            )
        assert exit_code == 0
        # Only "requests" and "flask" should be passed
        call_args = MockDL.return_value.download_many_sync.call_args
        assert call_args[0][0] == ["requests", "flask"]


# ---------------------------------------------------------------------------
# fetch-metadata
# ---------------------------------------------------------------------------


class TestCLIFetchMetadata:
    def test_fetch_metadata_basic(self, tmp_path):
        with patch("pypi_librarian.__main__.FetchMetadata") as MockFM:
            MockFM.return_value.run.return_value = 5
            exit_code = main(
                ["fetch-metadata", "--dest", str(tmp_path), "--limit", "5"]
            )
        assert exit_code == 0

    def test_fetch_metadata_from_file(self, tmp_path):
        pkg_file = tmp_path / "names.txt"
        pkg_file.write_text("requests\nflask\n")

        with patch("pypi_librarian.__main__.FetchMetadata") as MockFM:
            MockFM.return_value.run.return_value = 2
            exit_code = main(
                [
                    "fetch-metadata",
                    "--dest",
                    str(tmp_path),
                    "--from-file",
                    str(pkg_file),
                ]
            )
        assert exit_code == 0
        # Should pass names list to run()
        call_args = MockFM.return_value.run.call_args
        assert call_args[0][0] == ["requests", "flask"]

    def test_fetch_metadata_file_not_found(self):
        exit_code = main(["fetch-metadata", "--from-file", "/nonexistent/file.txt"])
        assert exit_code == 1
