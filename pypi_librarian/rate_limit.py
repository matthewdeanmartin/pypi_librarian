# coding=utf-8
"""
Rate limiting and retry infrastructure for PyPI HTTP requests.

Provides:
- ``AsyncTokenBucket`` — async token-bucket rate limiter (default 10 req/s)
- ``RateLimiter`` — combines token bucket with 429/Retry-After handling
- ``retry_on_transient`` — tenacity retry decorator for transient HTTP errors
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

__all__ = ["AsyncTokenBucket", "RateLimiter", "SyncTokenBucket", "retry_on_transient"]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Token bucket — async
# ---------------------------------------------------------------------------


class AsyncTokenBucket:
    """
    Async token-bucket rate limiter.

    Args:
        rate: Maximum requests per second.
        burst: Maximum burst size (defaults to *rate*).
    """

    def __init__(self, rate: float = 10.0, burst: float | None = None) -> None:
        self.rate = rate
        self.burst = burst if burst is not None else rate
        self._tokens = self.burst
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a token is available, then consume one."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait_time = (1.0 - self._tokens) / self.rate
            await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_refill = now


# ---------------------------------------------------------------------------
# Token bucket — sync
# ---------------------------------------------------------------------------


class SyncTokenBucket:
    """
    Sync token-bucket rate limiter for blocking code paths.

    Args:
        rate: Maximum requests per second.
        burst: Maximum burst size (defaults to *rate*).
    """

    def __init__(self, rate: float = 10.0, burst: float | None = None) -> None:
        self.rate = rate
        self.burst = burst if burst is not None else rate
        self._tokens = self.burst
        self._last_refill = time.monotonic()

    def acquire(self) -> None:
        """Block until a token is available, then consume one."""
        while True:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            wait_time = (1.0 - self._tokens) / self.rate
            time.sleep(wait_time)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_refill = now


# ---------------------------------------------------------------------------
# 429 / Retry-After handling
# ---------------------------------------------------------------------------


def _is_transient(exc: BaseException) -> bool:
    """Return True for HTTP errors worth retrying."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError)):
        return True
    return False


def _log_retry(state: RetryCallState) -> None:
    exc = state.outcome.exception() if state.outcome else None
    logger.warning(
        "Retry attempt %d after %s: %s",
        state.attempt_number,
        type(exc).__name__ if exc else "unknown",
        exc,
    )


retry_on_transient: Any = retry(
    retry=retry_if_exception(_is_transient),
    wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
    stop=stop_after_attempt(5),
    before_sleep=_log_retry,
    reraise=True,
)
"""Tenacity retry decorator: retries on 429, 5xx, timeouts. Max 5 attempts with jittered backoff."""


# ---------------------------------------------------------------------------
# RateLimiter — combines bucket + Retry-After awareness
# ---------------------------------------------------------------------------


class RateLimiter:
    """
    Combines an async token bucket with 429/Retry-After header awareness.

    Usage::

        limiter = RateLimiter(rate=10)
        await limiter.acquire()
        response = await client.get(url)
        await limiter.on_response(response)
    """

    def __init__(self, rate: float = 10.0) -> None:
        self.bucket = AsyncTokenBucket(rate=rate)

    async def acquire(self) -> None:
        """Wait for a token from the bucket."""
        await self.bucket.acquire()

    async def on_response(self, response: httpx.Response) -> None:
        """
        Handle rate-limit responses.

        If the server sends a 429 with ``Retry-After``, sleep for that
        duration before returning.
        """
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            delay = 5.0  # default backoff
            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = 5.0
            logger.warning("429 Too Many Requests — backing off %.1fs", delay)
            await asyncio.sleep(delay)
