# coding=utf-8
"""
Unit tests for pypi_librarian.utils.
"""

from __future__ import annotations

import asyncio
import os
import threading

import pytest

from pypi_librarian.utils import locate_file, run_async


class TestLocateFile:
    def test_locate_file_success(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")

        # Test locating a file that exists
        result = locate_file("test.txt", str(tmp_path / "other.py"))
        assert result == str(f)

    def test_locate_file_not_found(self, tmp_path):
        # Test locating a file that doesn't exist
        with pytest.raises(TypeError) as excinfo:
            locate_file("missing.txt", str(tmp_path / "other.py"))
        assert "doesn't exist" in str(excinfo.value)


class TestRunAsyncExtended:
    def test_run_async_in_new_loop(self):
        async def add(a: int, b: int) -> int:
            return a + b

        assert run_async(add(2, 3)) == 5

    def test_run_async_in_running_loop(self):
        """
        Simulate calling run_async from within an already running event loop.
        We do this by starting a thread that runs an event loop, and from that
        loop we call run_async.
        """
        result_container = []

        async def inner_coro():
            return "success"

        def thread_target():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def wrapper():
                # This simulates being in a running loop (like Jupyter)
                # and calling run_async.
                return run_async(inner_coro())

            try:
                result = loop.run_until_complete(wrapper())
                result_container.append(result)
            finally:
                loop.close()

        thread = threading.Thread(target=thread_target)
        thread.start()
        thread.join()

        assert result_container == ["success"]
