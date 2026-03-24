# coding=utf-8
"""
Tests for the modernized FetchMetadata class.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from pypi_librarian.fetch_metadata import FetchMetadata


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sample_json_text(name: str = "test-pkg") -> str:
    return json.dumps({"info": {"name": name, "version": "1.0.0"}})


# ---------------------------------------------------------------------------
# FetchMetadata
# ---------------------------------------------------------------------------


class TestFetchMetadata:
    @pytest.mark.asyncio
    async def test_run_async_with_names(self, tmp_path):
        fm = FetchMetadata(dest_dir=tmp_path)

        with patch("pypi_librarian.fetch_metadata.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json_as_text = AsyncMock(
                side_effect=lambda n: _sample_json_text(n)
            )
            mock_api.close = AsyncMock()

            count = await fm.run_async(names=["alpha", "beta"])

        assert count == 2
        assert (tmp_path / "alpha.json").exists()
        assert (tmp_path / "beta.json").exists()

    @pytest.mark.asyncio
    async def test_run_async_skips_existing(self, tmp_path):
        # Pre-create alpha.json
        (tmp_path / "alpha.json").write_text("{}")

        fm = FetchMetadata(dest_dir=tmp_path)

        with patch("pypi_librarian.fetch_metadata.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json_as_text = AsyncMock(
                side_effect=lambda n: _sample_json_text(n)
            )
            mock_api.close = AsyncMock()

            count = await fm.run_async(names=["alpha", "beta"])

        assert count == 1  # only beta
        # alpha.json should still have the original content
        assert json.loads((tmp_path / "alpha.json").read_text()) == {}

    @pytest.mark.asyncio
    async def test_run_async_with_limit(self, tmp_path):
        fm = FetchMetadata(dest_dir=tmp_path, limit=1)

        with patch("pypi_librarian.fetch_metadata.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json_as_text = AsyncMock(
                side_effect=lambda n: _sample_json_text(n)
            )
            mock_api.close = AsyncMock()

            count = await fm.run_async(names=["alpha", "beta", "gamma"])

        assert count == 1  # limited to 1

    @pytest.mark.asyncio
    async def test_run_async_handles_404(self, tmp_path):
        fm = FetchMetadata(dest_dir=tmp_path)

        with patch("pypi_librarian.fetch_metadata.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json_as_text = AsyncMock(return_value=None)
            mock_api.close = AsyncMock()

            count = await fm.run_async(names=["ghost-pkg"])

        assert count == 0
        assert not (tmp_path / "ghost-pkg.json").exists()

    def test_run_sync_wrapper(self, tmp_path):
        fm = FetchMetadata(dest_dir=tmp_path)

        with patch("pypi_librarian.fetch_metadata.AsyncJsonEndpoints") as MockAPI:
            mock_api = MockAPI.return_value
            mock_api.package_json_as_text = AsyncMock(
                side_effect=lambda n: _sample_json_text(n)
            )
            mock_api.close = AsyncMock()

            count = fm.run(names=["alpha"])

        assert count == 1

    @pytest.mark.asyncio
    async def test_run_async_empty_list(self, tmp_path):
        fm = FetchMetadata(dest_dir=tmp_path)
        count = await fm.run_async(names=[])
        assert count == 0
