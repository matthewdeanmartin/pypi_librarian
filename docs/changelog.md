# Changelog

## Unreleased

### Phase 2 — Async HTTP, bulk operations, resilience

- Migrated HTTP client from `requests` to `httpx` (supports both sync and async)
- Added `run_async()` helper so sync callers can invoke async methods without managing an event loop
- Added concurrent `get_many_projects_async()` and `get_many_packages_async()` with bounded concurrency
- Implemented `Downloader` with SHA-256 checksum verification
- Added resume / checkpoint support for interrupted bulk downloads (NDJSON checkpoint files)
- Modernised `FetchMetadata` to run async internally with sync wrappers
- Added token-bucket rate limiter with automatic `Retry-After` handling
- Added bulk CLI commands: `download`, `download-many`, `fetch-metadata`

### Phase 1 — Foundation

- Fixed broken `all_releases` and `get_packages` methods
- Replaced ad-hoc dicts with typed frozen dataclasses (`Project`, `Package`, `Release`, `ReleaseFile`, `ProjectInfo`, `User`)
- Added `.raw` passthrough on every model for schema resilience
- Wrapped JSON, HTML, and RSS PyPI endpoints in dedicated classes
- Introduced `Repository` as the single primary entry point
- Added unit tests and integration tests (gated behind `@pytest.mark.integration`)
- Added minimal CLI: `info`, `versions`, `latest`
