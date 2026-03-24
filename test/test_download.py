# coding=utf-8
"""
Tests for the Downloader, DownloadResult, DownloadPolicy, and checkpoint logic.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pypi_librarian.download import (
    DownloadPolicy,
    DownloadResult,
    Downloader,
    _Checkpoint,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_package_json(name: str = "test-pkg", version: str = "1.0.0") -> dict:
    """Minimal PyPI JSON API response for download tests."""
    content = b"fake wheel content for testing"
    sha256 = hashlib.sha256(content).hexdigest()
    return {
        "info": {"name": name, "version": version},
        "urls": [
            {
                "filename": f"{name}-{version}-py3-none-any.whl",
                "url": f"https://files.pythonhosted.org/packages/{name}-{version}-py3-none-any.whl",
                "size": len(content),
                "digests": {"md5": "abc123", "sha256": sha256},
                "packagetype": "bdist_wheel",
                "python_version": "py3",
                "requires_python": ">=3.10",
            },
            {
                "filename": f"{name}-{version}.tar.gz",
                "url": f"https://files.pythonhosted.org/packages/{name}-{version}.tar.gz",
                "size": len(content),
                "digests": {"md5": "def456", "sha256": sha256},
                "packagetype": "sdist",
                "python_version": "source",
                "requires_python": ">=3.10",
            },
        ],
    }


FAKE_CONTENT = b"fake wheel content for testing"
FAKE_SHA256 = hashlib.sha256(FAKE_CONTENT).hexdigest()


# ---------------------------------------------------------------------------
# DownloadPolicy
# ---------------------------------------------------------------------------


class TestDownloadPolicy:
    def test_defaults(self):
        policy = DownloadPolicy()
        assert policy.file_types == ["bdist_wheel", "sdist"]
        assert policy.max_workers == 10
        assert policy.rate_limit == 10.0
        assert policy.verify_checksums is True

    def test_custom(self):
        policy = DownloadPolicy(
            file_types=["bdist_wheel"],
            max_workers=5,
            rate_limit=5.0,
            verify_checksums=False,
        )
        assert policy.file_types == ["bdist_wheel"]
        assert policy.max_workers == 5


# ---------------------------------------------------------------------------
# DownloadResult
# ---------------------------------------------------------------------------


class TestDownloadResult:
    def test_defaults(self):
        r = DownloadResult(name="pkg", version="1.0")
        assert r.files == []
        assert r.errors == []
        assert r.skipped == []
        assert r.checksum_ok is True


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------


class TestCheckpoint:
    def test_new_checkpoint_is_empty(self, tmp_path):
        cp = _Checkpoint(tmp_path / "checkpoint.ndjson")
        assert not cp.is_done("pkg", "1.0")

    def test_mark_done_and_check(self, tmp_path):
        cp = _Checkpoint(tmp_path / "checkpoint.ndjson")
        result = DownloadResult(name="pkg", version="1.0", files=["a.whl"])
        cp.mark_done(result)
        assert cp.is_done("pkg", "1.0")
        assert not cp.is_done("pkg", "2.0")

    def test_persistence_across_instances(self, tmp_path):
        path = tmp_path / "checkpoint.ndjson"
        cp1 = _Checkpoint(path)
        cp1.mark_done(DownloadResult(name="pkg", version="1.0", files=["a.whl"]))

        cp2 = _Checkpoint(path)
        assert cp2.is_done("pkg", "1.0")

    def test_duplicate_mark_no_duplicate_lines(self, tmp_path):
        path = tmp_path / "checkpoint.ndjson"
        cp = _Checkpoint(path)
        result = DownloadResult(name="pkg", version="1.0", files=["a.whl"])
        cp.mark_done(result)
        cp.mark_done(result)  # duplicate
        lines = [l for l in path.read_text().strip().split("\n") if l]
        assert len(lines) == 1


# ---------------------------------------------------------------------------
# Downloader — download_one
# ---------------------------------------------------------------------------


class TestDownloaderDownloadOne:
    @pytest.mark.asyncio
    async def test_download_one_not_found(self, tmp_path):
        dl = Downloader(dest_dir=tmp_path)
        with patch("pypi_librarian.download.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json = AsyncMock(return_value=None)
            mock_api.close = AsyncMock()

            result = await dl.download_one("no-such-pkg")

        assert result.errors
        assert result.files == []

    @pytest.mark.asyncio
    async def test_download_one_success(self, tmp_path):
        dl = Downloader(dest_dir=tmp_path, policy=DownloadPolicy(verify_checksums=False))
        pkg_data = _fake_package_json()

        with patch("pypi_librarian.download.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json = AsyncMock(return_value=pkg_data)
            mock_api.close = AsyncMock()

            with patch.object(dl, "_download_file", new_callable=AsyncMock) as mock_dl:
                result = await dl.download_one("test-pkg")

        assert result.name == "test-pkg"
        assert result.version == "1.0.0"
        assert len(result.files) == 2  # wheel + sdist
        assert mock_dl.call_count == 2

    @pytest.mark.asyncio
    async def test_download_one_filters_by_type(self, tmp_path):
        policy = DownloadPolicy(file_types=["bdist_wheel"], verify_checksums=False)
        dl = Downloader(dest_dir=tmp_path, policy=policy)
        pkg_data = _fake_package_json()

        with patch("pypi_librarian.download.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json = AsyncMock(return_value=pkg_data)
            mock_api.close = AsyncMock()

            with patch.object(dl, "_download_file", new_callable=AsyncMock):
                result = await dl.download_one("test-pkg")

        assert len(result.files) == 1  # only wheel
        assert len(result.skipped) == 1  # sdist skipped

    @pytest.mark.asyncio
    async def test_download_one_specific_version(self, tmp_path):
        dl = Downloader(dest_dir=tmp_path, policy=DownloadPolicy(verify_checksums=False))
        pkg_data = _fake_package_json(version="2.0.0")

        with patch("pypi_librarian.download.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_version_json = AsyncMock(return_value=pkg_data)
            mock_api.close = AsyncMock()

            with patch.object(dl, "_download_file", new_callable=AsyncMock):
                result = await dl.download_one("test-pkg", version="2.0.0")

        assert result.version == "2.0.0"


# ---------------------------------------------------------------------------
# Downloader — download_many
# ---------------------------------------------------------------------------


class TestDownloaderDownloadMany:
    @pytest.mark.asyncio
    async def test_download_many_returns_results_for_all(self, tmp_path):
        dl = Downloader(dest_dir=tmp_path, policy=DownloadPolicy(verify_checksums=False))

        with patch.object(dl, "download_one", new_callable=AsyncMock) as mock_one:
            mock_one.return_value = DownloadResult(
                name="pkg", version="1.0", files=["a.whl"]
            )
            results = await dl.download_many(["pkg1", "pkg2"])

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_download_many_handles_exception(self, tmp_path):
        dl = Downloader(dest_dir=tmp_path)

        async def _fail(name, version=None):
            raise RuntimeError("boom")

        with patch.object(dl, "download_one", side_effect=_fail):
            results = await dl.download_many(["pkg1"])

        assert len(results) == 1
        assert results[0].errors
        assert "RuntimeError" in results[0].errors[0]


# ---------------------------------------------------------------------------
# Downloader — go_or_resume
# ---------------------------------------------------------------------------


class TestDownloaderResume:
    @pytest.mark.asyncio
    async def test_resume_skips_checkpointed(self, tmp_path):
        # Pre-populate checkpoint
        cp_path = tmp_path / ".pypi_checkpoint.ndjson"
        cp_path.write_text(
            json.dumps({"name": "done-pkg", "version": "1.0", "files": ["a.whl"], "errors": []}) + "\n"
        )

        dl = Downloader(dest_dir=tmp_path, policy=DownloadPolicy(verify_checksums=False))

        with patch("pypi_librarian.download.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            # For "done-pkg" version resolution
            mock_api.package_json = AsyncMock(
                side_effect=lambda n: _fake_package_json(n, "1.0") if n == "done-pkg" else _fake_package_json(n, "2.0")
            )
            mock_api.close = AsyncMock()

            with patch.object(dl, "download_many", new_callable=AsyncMock) as mock_many:
                mock_many.return_value = [
                    DownloadResult(name="new-pkg", version="2.0", files=["b.whl"])
                ]
                results = await dl.go_or_resume(["done-pkg", "new-pkg"])

        # done-pkg should be skipped (checkpoint), new-pkg should be downloaded
        skipped = [r for r in results if r.skipped]
        downloaded = [r for r in results if r.files]
        assert len(skipped) == 1
        assert skipped[0].name == "done-pkg"
        assert len(downloaded) == 1
        assert downloaded[0].name == "new-pkg"


# ---------------------------------------------------------------------------
# Downloader — sync wrappers
# ---------------------------------------------------------------------------


class TestDownloaderSync:
    def test_download_one_sync(self, tmp_path):
        dl = Downloader(dest_dir=tmp_path, policy=DownloadPolicy(verify_checksums=False))

        with patch("pypi_librarian.download.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json = AsyncMock(return_value=_fake_package_json())
            mock_api.close = AsyncMock()

            with patch.object(dl, "_download_file", new_callable=AsyncMock):
                result = dl.download_one_sync("test-pkg")

        assert result.name == "test-pkg"
        assert len(result.files) == 2


# ---------------------------------------------------------------------------
# Checksum verification
# ---------------------------------------------------------------------------


class TestChecksumVerification:
    @pytest.mark.asyncio
    async def test_checksum_mismatch_removes_file(self, tmp_path):
        dl = Downloader(dest_dir=tmp_path, policy=DownloadPolicy(verify_checksums=True))
        bad_data = _fake_package_json()
        # Set wrong checksum
        bad_data["urls"][0]["digests"]["sha256"] = "wrong_hash"
        # Only include the wheel
        bad_data["urls"] = [bad_data["urls"][0]]

        async def _fake_download(url, dest, expected_sha256):
            # Write content that won't match the expected hash
            dest.write_bytes(b"actual content")
            actual_hash = hashlib.sha256(b"actual content").hexdigest()
            if expected_sha256 and actual_hash != expected_sha256:
                from pypi_librarian.download import _ChecksumMismatch
                dest.unlink()
                raise _ChecksumMismatch(f"SHA256 mismatch")

        with patch("pypi_librarian.download.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json = AsyncMock(return_value=bad_data)
            mock_api.close = AsyncMock()

            with patch.object(dl, "_download_file", side_effect=_fake_download):
                result = await dl.download_one("test-pkg")

        assert result.checksum_ok is False
        assert len(result.errors) == 1
