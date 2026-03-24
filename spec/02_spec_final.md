# PyPI Librarian — Final Spec & Phased Roadmap

## Core Identity

`pypi_librarian` is a **programmer-friendly Python library** for querying and consuming PyPI data. It is not a package installer, not a mirror tool, not an uploader — it is a **data access and bulk-download library** for people who want to work with PyPI programmatically.

### Primary Use Cases

1. **Single-package queries**: Get clean, typed metadata for one package or version. Ergonomic and REPL-friendly.
2. **Bulk download**: Download many packages' distributions or metadata — for static analysis, mirror seeds, research, or tooling tests.
3. **Change monitoring**: Watch PyPI for new packages and updates via RSS/feeds.
4. **Data enrichment & analytics**: Join PyPI data with external sources (downloads, GitHub, security) for research and scoring.

### Design Principles (synthesized from both spec docs)

- **Data-first, not request-first**: Return typed models, not raw response objects.
- **Dual models**: Strong typed dataclasses for stable fields + `raw: dict` passthrough for future PyPI fields.
- **Composable**: Works in scripts, pipelines, REPL sessions, and services.
- **Offline-friendly**: Caching is a first-class concern, not an afterthought.
- **Polite by default**: Client-side rate limiting baked in; won't hammer PyPI.
- **Resilient to schema drift**: PyPI adds fields constantly; don't break on unknown fields.
- **Type-annotated throughout**: `__all__` on every public module; Python 3.10+.

---

## What Exists Today (Baseline Assessment)

### Working
- `JsonEndpoints`: GET `/pypi/{package}/json` and `/pypi/{package}/{version}/json`
- `HtmlEndpoints`: fetch project page, user page, all packages from `/simple/`
- `RssEndpoints`: fetch `/rss/packages.xml` and `/rss/updates.xml` (raw text, unparsed)
- `Repository`, `Project`, `Package`, `User` class hierarchy (partially wired up)
- `FetchMetadata`: bulk metadata download loop with resume-by-file logic
- Basic tests against live PyPI (integration tests only)

### Stubbed / Broken
- `Downloader`: class exists, all methods raise `NotImplementedError`
- `Project.all_releases()`: has a bug — `items(0)` instead of `items()`
- `User.get_packages()`: `NotImplementedError`
- `Repository.projects_by_user()`: returns empty list
- `Repository.search_projects()`: returns empty list
- `Package.stats()`: returns `None`
- `meta_file.py`: empty stub
- `pypi_versions.py`: shell-scripty, uses `curl` subprocess — not library-grade
- CLI (`__main__.py`): prints "Not supported yet"
- RSS feeds: raw text, no parsing

### Recently Deleted (in "Massive upgrade" commit)
- `pip_endpoints.py`, `qypi_endpoints.py`, `xml_rpc_endpoints.py`, `yolk_endpoints.py`
- Tests: `test_doc_opts.py`, `test_package_downloader.py`, `test_search.py`, `test_version_check.py`
- `FetchMetadata` still references deleted `qypi_endpoints.info()` — **active bug**

---

## What to Scope In vs. Out

### In Scope (realistic ambition)
- Ergonomic single-package and single-version queries
- Typed dataclass models with `raw` passthrough
- Bulk metadata download (all packages or filtered subset)
- Distribution file download (wheels, sdists) with checksum verification
- RSS feed parsing (new packages, updates)
- HTML `/simple/` API scraping for package enumeration
- Disk-based caching (SQLite or file-based)
- Rate limiting with retry/backoff
- Serialization to JSON, TOML, YAML (optional: Parquet, NDJSON for analytics)
- Basic CLI for single-package queries and download
- Download stats via pypistats.org API
- Optional GitHub metadata enrichment
- Async variant of the HTTP layer (optional/bonus)

### Out of Scope (explicitly deferred)
- Package installation (that's pip)
- Full mirroring / bandersnatch replacement
- LLM integration
- SBOM generation
- Snapshot/time-travel installs
- Redis caching tier
- Plugin/extensibility system (design for it, don't implement it yet)
- Reverse dependency graph queries (depends on data not in PyPI API)
- CVE/NVD feed joining (use osv.dev if needed, don't build it)

---

## Phase Roadmap

---

### Phase 1 — Solid Foundation (Core API, no frills)

**Goal**: A library someone can `pip install` and immediately use to query PyPI. No stubs. No broken methods.

**Deliverables**:

1. **Fix all broken/stubbed core methods**
   - `Project.all_releases()`: fix the `items(0)` bug
   - `User.get_packages()`: implement via JSON API (not XML-RPC which is deprecated)
   - `Repository.projects_by_user()`: implement via HTML user page scraping or XML-RPC fallback
   - Remove or clearly mark `meta_file.py` and `pypi_versions.py` as internal/deprecated

2. **Typed dataclass models** (replace current plain classes)
   - `ProjectInfo`: top-level project metadata (name, summary, author, license, classifiers, requires_python, etc.)
   - `ReleaseFile`: a single distribution file (filename, url, size, digests, packagetype, python_version, requires_python)
   - `Release`: a version with a list of `ReleaseFile`
   - `Project`: name + all releases + `raw: dict`
   - `Package`: a specific version's full metadata + `raw: dict`
   - `User`: name + list of maintained package names
   - All models use `@dataclass(frozen=True)` where appropriate; expose `.raw` for unknown fields

3. **Clean up endpoint layer**
   - `JsonEndpoints`: keep, add type hints, return parsed dicts not raw responses
   - `HtmlEndpoints`: keep, fix/document that `/simple/` is the Simple Repository API (PEP 503)
   - `RssEndpoints`: parse RSS XML into typed feed items (`NewPackage`, `UpdatedPackage`) instead of returning raw text
   - Remove all subprocess/shell command usage from library code (`pypi_versions.py`)

4. **Repository as the primary entry point**
   - `Repository.get_project(name) -> Project`
   - `Repository.get_package(name, version) -> Package`
   - `Repository.get_user(name) -> User`
   - `Repository.get_all_package_names() -> Iterator[str]` (from `/simple/`)
   - `Repository.latest_releases(count=40) -> list[NewRelease]` (from RSS)
   - `Repository.newest_packages(count=40) -> list[NewPackage]` (from RSS)

5. **Unit + integration tests**
   - Unit tests for model construction (no network)
   - Integration tests tagged `@pytest.mark.integration` (network, skippable in CI)
   - Fix `FetchMetadata` reference to deleted `qypi_endpoints`

6. **Minimal working CLI**
   - `pypi-librarian info <package>`: print package metadata
   - `pypi-librarian versions <package>`: list all versions
   - `pypi-librarian latest`: print newest packages from RSS
   - Use `argparse`, clean error codes, logging flag `--log-level`

**What phase 1 does NOT include**: caching, rate limiting, bulk download, serialization formats.

---

### Phase 2 — Bulk Download & Resilience

**Goal**: Make the bulk download story real. This is the library's key differentiator from simple API wrappers.

**Deliverables**:

1. **`Downloader` — fully implemented**
   - Constructor: `Downloader(packages, dest_dir, policy)`
   - Policy options: `unzip: bool`, `keep_zips: bool`, `file_types: list[str]` (wheel, sdist, etc.), `max_workers: int`
   - `download_one(name, version=None) -> DownloadResult`
   - `download_many(names: Iterable[str]) -> Iterator[DownloadResult]` — parallel, generator-based
   - Checksum verification against PyPI-provided digests (SHA256)
   - `DownloadResult`: dataclass with `name`, `version`, `files`, `errors`, `skipped`

2. **Resume / fault tolerance**
   - Track completed packages in a simple checkpoint file (NDJSON per-line)
   - On restart, skip already-downloaded packages
   - Partial results on per-package failure — don't abort the whole batch
   - `go_or_resume()` reads checkpoint, skips done, continues

3. **`FetchMetadata` — modernized**
   - Remove dependency on deleted `qypi_endpoints`
   - Source package list from `/simple/` (live) or a local snapshot file
   - Output: one `.json` file per package in target dir
   - Resume logic: skip packages whose `.json` already exists
   - Configurable concurrency

4. **Rate limiting**
   - Wrap all HTTP calls with a token-bucket limiter (use `tenacity` for retry/backoff)
   - Default: 10 req/sec with jitter
   - Respect `Retry-After` headers on 429
   - Configurable: `Repository(rate_limit="5/sec")`

5. **Bulk CLI commands**
   - `pypi-librarian download <package> [--version V] [--dest DIR]`
   - `pypi-librarian download-many --from-file packages.txt [--dest DIR] [--workers N]`
   - `pypi-librarian fetch-metadata [--dest DIR] [--limit N]`

---

### Phase 3 — Caching & Serialization

**Goal**: Make repeated queries cheap and enable offline workflows.

**Deliverables**:

1. **Disk cache (SQLite-backed)**
   - `Repository(cache="sqlite:///pypi_cache.db")` or `cache="~/.cache/pypi_librarian/"`
   - Cache JSON API responses keyed by `(package, version)` with TTL
   - Smart invalidation: check ETag/Last-Modified before re-fetching
   - Memory LRU cache as first tier (in-process, small)
   - `cache.query(sql)` passthrough for SQLite backends

2. **Serialization**
   - Every model supports `.to_json()`, `.to_toml()`, `.to_yaml()`
   - Collections support `.to_ndjson()` (streaming, line-delimited)
   - Optional extras: `.to_parquet()` (requires `pyarrow`), `.to_csv()`
   - `Repository.get_project("requests").to("parquet", "requests.parquet")`

3. **`Repository.stream_projects()`**
   - Generator: yields `Project` objects one at a time
   - Backed by `/simple/` enumeration + JSON API per package
   - Supports `.take(N)`, `.filter(predicate)`, `.to_ndjson(path)`
   - Memory-efficient: never loads all packages at once

4. **CLI serialization flags**
   - `pypi-librarian info requests --format yaml`
   - `pypi-librarian info requests --format toml`

---

### Phase 4 — Data Enrichment & Analytics

**Goal**: Join PyPI data with external signals to enable research, scoring, and monitoring.

**Deliverables**:

1. **Download stats via pypistats.org**
   - `package.downloads.last_day`, `.last_week`, `.last_month`
   - Fetched from `https://pypistats.org/api/packages/{name}/recent`
   - Cached aggressively (stats change daily)

2. **GitHub enrichment (optional)**
   - Extract GitHub URL from project metadata
   - Fetch: stars, open issues, last commit date, CI badge presence
   - `package.github.stars`, `package.github.last_commit`
   - Requires GitHub token for rate limits; gracefully skips if absent

3. **Basic health/activity scoring**
   - `package.health_score()` → float 0–1
   - Inputs: release cadence, requires_python recency, has README, has classifiers, download trend
   - Simple weighted heuristic, not ML

4. **Analytics queries on cached data**
   - `client.cache.query("SELECT name FROM projects WHERE last_release < '2020-01-01'")`
   - Helper methods: `client.analytics.stale_packages(years=3)`, `client.analytics.packages_missing_classifiers()`

5. **Enrichment CLI**
   - `pypi-librarian enrich requests --with downloads,github`
   - `pypi-librarian analytics stale --years 3 --format csv`

---

### Phase 5 — Async, Provenance & Polish

**Goal**: Production-grade quality. Async support. Trust metadata.

**Deliverables**:

1. **Async HTTP layer**
   - `AsyncRepository` using `httpx` instead of `requests`
   - `await client.get_project("requests")`
   - All bulk operations natively async
   - Sync wrappers remain for backwards compatibility

2. **Provenance tracking**
   - `ReleaseFile.provenance`: source, hash algorithm + digest, verified (bool)
   - Verify downloaded files against PyPI-provided digests
   - Detect and report yanked releases
   - `package.provenance.attested` if PyPI attestations present (PEP 740)

3. **Schema introspection & forward compatibility**
   - `Repository.discover_schema()` → current API shape
   - Warn (not crash) on unexpected fields; log them for user visibility
   - Feature flag mechanism: `Repository(features=["new-metadata-v2"])`

4. **Plugin/extensibility hooks**
   - `Repository.register_enricher(MyPlugin())` — simple interface
   - `EnricherBase` abstract class: `enrich(package: Package) -> Package`
   - No plugin registry/discovery yet — just a clean extension point

5. **Full CLI parity**
   - Every library operation accessible via CLI
   - Machine-readable output (`--format json/yaml/toml/ndjson`)
   - Shell-friendly exit codes (0 success, 1 not found, 2 network error, etc.)
   - `--log-level DEBUG/INFO/WARNING/ERROR`

---

## Feature Summary by Phase

| Feature | Phase |
|---|---|
| Fix broken stubs (`all_releases`, `get_packages`) | 1 |
| Typed dataclass models with `.raw` passthrough | 1 |
| JSON API endpoint wrappers (clean) | 1 |
| RSS feed parsing (typed results) | 1 |
| HTML `/simple/` enumeration | 1 |
| Minimal CLI (`info`, `versions`, `latest`) | 1 |
| Unit + integration tests | 1 |
| `Downloader` — single and bulk | 2 |
| Checksum verification | 2 |
| Resume / checkpoint logic | 2 |
| `FetchMetadata` modernized | 2 |
| Rate limiting + retry/backoff | 2 |
| Bulk CLI (`download`, `download-many`, `fetch-metadata`) | 2 |
| Disk cache (SQLite) | 3 |
| Memory LRU cache | 3 |
| ETag / TTL cache invalidation | 3 |
| `.to_json()`, `.to_toml()`, `.to_yaml()` | 3 |
| `.to_ndjson()` streaming | 3 |
| `.to_parquet()` (optional extra) | 3 |
| `stream_projects()` generator | 3 |
| pypistats download counts | 4 |
| GitHub enrichment (optional) | 4 |
| Health/activity scoring | 4 |
| Analytics queries on cache | 4 |
| `AsyncRepository` (httpx) | 5 |
| Provenance / digest verification | 5 |
| Yanked release detection | 5 |
| PEP 740 attestation awareness | 5 |
| Schema introspection / forward-compat | 5 |
| Plugin/enricher extension point | 5 |
| Full CLI parity + exit codes | 5 |

---

## Technical Decisions & Constraints

### HTTP Client
- Phase 1–4: `requests` (already a dependency, synchronous, simpler)
- Phase 5: add `httpx` for async; keep `requests` for sync path

### Data Models
- Use `@dataclass` not Pydantic (per spec: "use all the good features of dataclasses, not pydantic")
- `frozen=True` where immutability makes sense (release files, digests)
- `raw: dict[str, Any]` field on all top-level models

### Caching
- Phase 3: SQLite via stdlib `sqlite3` (no extra dep) for disk cache
- File-based cache (one JSON file per package) as simpler alternative
- No Redis tier planned until there's a concrete need

### Rate Limiting
- Use `tenacity` for retry/backoff (already mentioned in spec, standard library)
- Simple token bucket in pure Python for rate limiting (no extra dep needed)

### Serialization
- JSON: stdlib `json`
- TOML: `tomllib` (stdlib 3.11+) for read, `tomli-w` for write
- YAML: `pyyaml` (optional dep)
- Parquet: `pyarrow` (optional dep, heavy)

### CLI
- `argparse` (stdlib, per architecture spec — "argparse, all the good features")
- Replace current `docopt` dependency
- Entry point: `pypi-librarian` command

### Testing
- Split integration tests into `@pytest.mark.integration`
- Use `responses` or `pytest-httpserver` to mock HTTP in unit tests
- Keep live integration tests but gate them behind a marker

### Python Version
- Python 3.10+ (per architecture spec)
- Drop Python 3.8 support

---

## What the Spec Ideas That Are Deferred Mean in Practice

The spec documents contain ambitious ideas (time-travel, LLM, SBOM, reverse deps). These aren't being abandoned — they're being filed under "once the foundation is solid, these become possible." Specifically:

- **Snapshot mirror** (time-travel installs) requires the caching layer (Phase 3) as a prerequisite
- **Reverse deps** (`used_by`) requires either a pre-built index or scraping — revisit after Phase 4 analytics infrastructure
- **LLM integration** is a thin wrapper once bulk metadata + streaming exist (Phase 3+)
- **SBOM generation** needs provenance (Phase 5) as a prerequisite
- **SQL query layer** over PyPI data becomes natural once SQLite caching exists (Phase 3+)
