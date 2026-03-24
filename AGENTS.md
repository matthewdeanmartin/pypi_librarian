# AGENTS.md — Notes for AI agents working on this project

## Build & Run Commands

- **Always use `uv run`** to execute commands. Never use bare `python`, `pip install`, or `python -m pytest`. Examples:
  ```bash
  uv run pytest -m "not integration" -x -v
  uv run mypy pypi_librarian
  uv run ruff check .
  uv run python -m pypi_librarian info requests
  ```
- Dependencies are managed in `pyproject.toml` under `[project.dependencies]` and `[dependency-groups]`. `uv` resolves and installs them automatically — do not run `pip install` separately.

## Testing

- **Unit vs integration**: Integration tests are marked `@pytest.mark.integration` and require live network access to PyPI. Run unit tests only with `-m "not integration"`.
- **asyncio_mode = "auto"** is set in `pyproject.toml`. Async test functions are detected automatically — you still need `@pytest.mark.asyncio` on async test methods inside classes, but standalone async test functions work without it.
- **Mocking httpx**: This project uses `httpx`, not `requests`. When mocking HTTP responses, construct real `httpx.Response` objects — they require a `request=` kwarg:
  ```python
  httpx.Response(
      status_code=200,
      text=body,
      request=httpx.Request("GET", "https://test/"),
  )
  ```
  Do **not** use `MagicMock()` for HTTP responses — `httpx.Response` has properties that don't work with magic mocks (e.g., `.text` vs `.content` encoding).
- **Mocking endpoint classes**: The sync endpoint classes (`JsonEndpoints`, `HtmlEndpoints`, `RssEndpoints`) use lazy `httpx.Client` initialization via `_get_client()`. Mock at the method level (`_session_get`, `_fetch`, `_get_client`) rather than trying to patch the httpx module globally.
- **Mocking async bulk methods**: The `Repository` bulk methods (`get_many_projects_async`, etc.) create their own `AsyncJsonEndpoints` internally. Patch `pypi_librarian.class_repo.AsyncJsonEndpoints` (the class, at the import site) and set `return_value.package_json = AsyncMock(...)`.

## Architecture

- **Sync-first for single queries**: `JsonEndpoints`, `HtmlEndpoints`, `RssEndpoints` all use sync `httpx.Client`. Callers never need an event loop for simple operations like `repo.get_project("requests")`.
- **Async for bulk**: `AsyncJsonEndpoints` and `AsyncHtmlEndpoints` exist for concurrent operations. The `Repository` class exposes `_async` methods and sync wrappers that call `run_async()`.
- **`run_async()` in `utils.py`**: Bridges sync → async. Uses `asyncio.run()` normally, falls back to a thread pool if already inside a running loop (Jupyter, async REPL).
- **Models are pure dataclasses** in `models.py`. Factory functions (`_project_from_json`, etc.) are private — callers use `Repository` methods.
- **`lxml` is still used** for HTML parsing (`/simple/` page). It is not being replaced.
- **XML-RPC** is used for `packages_for_user()` — this is the only reliable way to get user package lists since PyPI blocks HTML scraping of user pages.

## Spec & Roadmap

- The canonical spec is `spec/02_spec_final.md`. It contains the phased roadmap.
- Phase 1 is complete (models, endpoints, Repository, CLI, tests).
- Phase 2 is the httpx/async migration + bulk download + resilience.
- Do not reference or import from deleted modules (`pip_endpoints`, `qypi_endpoints`, `xml_rpc_endpoints`, `yolk_endpoints`).

## Common Pitfalls

- **Don't add `requests` back**: The project migrated from `requests` to `httpx` in Phase 2. The `requests` package is no longer a dependency. If you see old code or tests referencing `requests`, update them to use `httpx`.
- **`httpx.Response.content` vs `.text`**: When mocking responses for HTML parsing (lxml), you need `.content` (bytes). Use the `content=` kwarg on `httpx.Response` constructor, not `text=`.
- **Endpoint `close()` methods**: All endpoint classes have a `close()` method. Use it in tests and in long-lived applications, but it's optional for scripts (garbage collection handles it).
