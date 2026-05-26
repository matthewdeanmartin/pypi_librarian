# coding=utf-8
"""
Utility functions for pypi_librarian.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Coroutine
from typing import Any, TypeVar

__all__ = ["locate_file", "run_async"]

T = TypeVar("T")


def run_async(coro: Coroutine[Any, Any, T], /) -> T:
    """
    Run an async coroutine from synchronous code and return the result.

    Usage::

        from pypi_librarian.utils import run_async

        results = run_async(repo.get_many_projects_async(["requests", "flask"]))

    If no event loop is running, uses :func:`asyncio.run`.
    If called from within an already-running loop (e.g. Jupyter), falls back
    to creating a new loop on a background thread.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(coro)

    # Already inside a running loop (e.g. Jupyter notebook, async REPL).
    # Run the coroutine in a new event loop on a separate thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future: concurrent.futures.Future[T] = pool.submit(asyncio.run, coro)
        return future.result()


def locate_file(file_name: str, executing_file: str) -> str:
    """
    File must exist
    :type file_name: str|unicode
    :type executing_file: str|unicode
    :return: str
    """
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(executing_file)), file_name
    )
    if not os.path.exists(file_path):
        raise TypeError(file_path + " doesn't exist")
    return file_path
