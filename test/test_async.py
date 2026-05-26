# coding=utf-8
"""
Tests for async functionality: AsyncJsonEndpoints, bulk Repository methods,
and run_async helper.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from pypi_librarian.json_endpoints import AsyncJsonEndpoints
from pypi_librarian.models import Package, Project
from pypi_librarian.utils import run_async

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _async_response(body: str, status: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status,
        text=body,
        request=httpx.Request("GET", "https://test/"),
    )


# ---------------------------------------------------------------------------
# run_async
# ---------------------------------------------------------------------------


class TestRunAsync:
    def test_runs_coroutine_from_sync(self):
        async def add(a: int, b: int) -> int:
            return a + b

        assert run_async(add(2, 3)) == 5

    def test_returns_result(self):
        async def greeting() -> str:
            return "hello"

        assert run_async(greeting()) == "hello"


# ---------------------------------------------------------------------------
# AsyncJsonEndpoints
# ---------------------------------------------------------------------------


class TestAsyncJsonEndpoints:
    @pytest.mark.asyncio
    async def test_package_json_returns_dict(self, sample_project_json):
        aje = AsyncJsonEndpoints()
        resp = _async_response(json.dumps(sample_project_json))
        with patch.object(aje, "_get", return_value=resp):
            result = await aje.package_json("test-pkg")
        assert isinstance(result, dict)
        assert result["info"]["name"] == "test-pkg"

    @pytest.mark.asyncio
    async def test_package_json_404_returns_none(self):
        aje = AsyncJsonEndpoints()
        resp = _async_response("", status=404)
        with patch.object(aje, "_get", return_value=resp):
            result = await aje.package_json("no-such-package")
        assert result is None

    @pytest.mark.asyncio
    async def test_package_version_json_returns_dict(self, sample_project_json):
        aje = AsyncJsonEndpoints()
        resp = _async_response(json.dumps(sample_project_json))
        with patch.object(aje, "_get", return_value=resp):
            result = await aje.package_version_json("test-pkg", "1.0.0")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_package_version_json_404_returns_none(self):
        aje = AsyncJsonEndpoints()
        resp = _async_response("", status=404)
        with patch.object(aje, "_get", return_value=resp):
            result = await aje.package_version_json("test-pkg", "99.99.99")
        assert result is None


# ---------------------------------------------------------------------------
# Repository bulk async methods (unit tests)
# ---------------------------------------------------------------------------


class TestRepositoryBulkAsync:
    @pytest.mark.asyncio
    async def test_get_many_projects_async(self, sample_project_json):
        from pypi_librarian.class_repo import Repository

        repo = Repository()
        resp = _async_response(json.dumps(sample_project_json))

        async def fake_get(*path: str) -> httpx.Response:
            return resp

        with patch("pypi_librarian.class_repo.AsyncJsonEndpoints") as MockAJE:
            mock_aje = MockAJE.return_value
            mock_aje.package_json = AsyncMock(return_value=sample_project_json)
            mock_aje.close = AsyncMock()

            results = await repo.get_many_projects_async(["test-pkg", "test-pkg"])

        assert len(results) == 2
        assert all(isinstance(p, Project) for p in results)

    @pytest.mark.asyncio
    async def test_get_many_projects_async_skips_not_found(self, sample_project_json):
        from pypi_librarian.class_repo import Repository

        repo = Repository()

        with patch("pypi_librarian.class_repo.AsyncJsonEndpoints") as MockAJE:
            mock_aje = MockAJE.return_value
            mock_aje.package_json = AsyncMock(side_effect=[sample_project_json, None])
            mock_aje.close = AsyncMock()

            results = await repo.get_many_projects_async(["test-pkg", "no-such"])

        assert len(results) == 1

    def test_get_many_projects_sync_wrapper(self, sample_project_json):
        from pypi_librarian.class_repo import Repository

        repo = Repository()

        with patch("pypi_librarian.class_repo.AsyncJsonEndpoints") as MockAJE:
            mock_aje = MockAJE.return_value
            mock_aje.package_json = AsyncMock(return_value=sample_project_json)
            mock_aje.close = AsyncMock()

            results = repo.get_many_projects(["test-pkg"])

        assert len(results) == 1
        assert isinstance(results[0], Project)

    @pytest.mark.asyncio
    async def test_get_many_packages_async(self, sample_project_json):
        from pypi_librarian.class_repo import Repository

        repo = Repository()

        with patch("pypi_librarian.class_repo.AsyncJsonEndpoints") as MockAJE:
            mock_aje = MockAJE.return_value
            mock_aje.package_version_json = AsyncMock(return_value=sample_project_json)
            mock_aje.close = AsyncMock()

            results = await repo.get_many_packages_async([("test-pkg", "1.0.0")])

        assert len(results) == 1
        assert isinstance(results[0], Package)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_async_json_endpoints_live():
    aje = AsyncJsonEndpoints()
    try:
        data = await aje.package_json("requests")
        assert data is not None
        assert data["info"]["name"] == "requests"
    finally:
        await aje.close()


@pytest.mark.integration
def test_get_many_projects_live():
    from pypi_librarian.class_repo import Repository

    repo = Repository()
    projects = repo.get_many_projects(["requests", "flask"])
    assert len(projects) == 2
    names = {p.name for p in projects}
    assert "requests" in names
    assert "flask" in names or "Flask" in names
