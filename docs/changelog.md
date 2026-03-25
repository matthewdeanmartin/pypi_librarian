# Changelog

## Unreleased

### Phase 4 — Data Enrichment & Analytics

- Added `pypistats.py`: `fetch_download_stats()` fetches last-day / last-week / last-month download counts from pypistats.org
- Added `github.py`: `fetch_github_info()` fetches stars, forks, open issues, last push date, and archived status from the GitHub REST API; `extract_github_repo()` extracts GitHub coordinates from package metadata URLs
- Added `health.py`: `score_project()` computes a 0–1 health score from PyPI metadata, optional pypistats data, and optional GitHub data with per-component breakdown and human-readable notes
- Added `Repository.get_download_stats()`, `Repository.get_github_info()`, and `Repository.health_score()` convenience methods
- Added `enrich` CLI command: `pypi-librarian enrich <package> [--with downloads,github,health] [--github-token TOKEN]`
- Exported `DownloadStats`, `GitHubInfo`, and `HealthScore` from top-level `pypi_librarian` package

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
