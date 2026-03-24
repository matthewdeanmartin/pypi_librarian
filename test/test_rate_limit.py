# coding=utf-8
"""
Tests for rate limiting infrastructure.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import httpx
import pytest

from pypi_librarian.rate_limit import (
    AsyncTokenBucket,
    RateLimiter,
    SyncTokenBucket,
    _is_transient,
)


# ---------------------------------------------------------------------------
# SyncTokenBucket
# ---------------------------------------------------------------------------


class TestSyncTokenBucket:
    def test_first_acquire_is_instant(self):
        bucket = SyncTokenBucket(rate=10.0)
        t0 = time.monotonic()
        bucket.acquire()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.05

    def test_burst_allows_multiple_immediate(self):
        bucket = SyncTokenBucket(rate=100.0, burst=5.0)
        t0 = time.monotonic()
        for _ in range(5):
            bucket.acquire()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.1

    def test_rate_limits_after_burst(self):
        # Rate = 2/s, burst = 1 → after 1 immediate, must wait ~0.5s
        bucket = SyncTokenBucket(rate=2.0, burst=1.0)
        bucket.acquire()  # immediate
        t0 = time.monotonic()
        bucket.acquire()  # should wait ~0.5s
        elapsed = time.monotonic() - t0
        assert elapsed >= 0.3  # some tolerance


# ---------------------------------------------------------------------------
# AsyncTokenBucket
# ---------------------------------------------------------------------------


class TestAsyncTokenBucket:
    @pytest.mark.asyncio
    async def test_first_acquire_is_instant(self):
        bucket = AsyncTokenBucket(rate=10.0)
        t0 = time.monotonic()
        await bucket.acquire()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.05

    @pytest.mark.asyncio
    async def test_burst_allows_multiple_immediate(self):
        bucket = AsyncTokenBucket(rate=100.0, burst=5.0)
        t0 = time.monotonic()
        for _ in range(5):
            await bucket.acquire()
        elapsed = time.monotonic() - t0
        assert elapsed < 0.1


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire_delegates_to_bucket(self):
        limiter = RateLimiter(rate=100.0)
        await limiter.acquire()  # should not raise

    @pytest.mark.asyncio
    async def test_on_response_429_sleeps(self):
        limiter = RateLimiter(rate=100.0)
        resp = httpx.Response(
            status_code=429,
            headers={"Retry-After": "0.1"},
            request=httpx.Request("GET", "https://test/"),
        )
        with patch("pypi_librarian.rate_limit.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            await limiter.on_response(resp)
            mock_sleep.assert_called_once_with(0.1)

    @pytest.mark.asyncio
    async def test_on_response_200_does_not_sleep(self):
        limiter = RateLimiter(rate=100.0)
        resp = httpx.Response(
            status_code=200,
            request=httpx.Request("GET", "https://test/"),
        )
        with patch("pypi_librarian.rate_limit.asyncio.sleep") as mock_sleep:
            await limiter.on_response(resp)
            mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# _is_transient
# ---------------------------------------------------------------------------


class TestIsTransient:
    def test_429_is_transient(self):
        resp = httpx.Response(
            status_code=429,
            request=httpx.Request("GET", "https://test/"),
        )
        exc = httpx.HTTPStatusError(
            "rate limited", request=resp.request, response=resp
        )
        assert _is_transient(exc) is True

    def test_500_is_transient(self):
        resp = httpx.Response(
            status_code=500,
            request=httpx.Request("GET", "https://test/"),
        )
        exc = httpx.HTTPStatusError(
            "server error", request=resp.request, response=resp
        )
        assert _is_transient(exc) is True

    def test_404_is_not_transient(self):
        resp = httpx.Response(
            status_code=404,
            request=httpx.Request("GET", "https://test/"),
        )
        exc = httpx.HTTPStatusError(
            "not found", request=resp.request, response=resp
        )
        assert _is_transient(exc) is False

    def test_timeout_is_transient(self):
        assert _is_transient(httpx.ReadTimeout("timeout")) is True
        assert _is_transient(httpx.ConnectTimeout("timeout")) is True

    def test_value_error_is_not_transient(self):
        assert _is_transient(ValueError("nope")) is False
