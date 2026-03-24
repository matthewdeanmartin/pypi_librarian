# pypi-librarian

A Python library and CLI tool for **querying and downloading PyPI package metadata and distribution files**.

pypi-librarian is not a package installer (like pip), a mirror tool (like bandersnatch), or an uploader (like twine). It is a **data-access library** built for:

- Researchers analyzing PyPI data at scale
- Static analysis and linting tools that need package metadata
- CI pipelines that need to inspect or download specific distributions
- Scripts that monitor PyPI for new packages and updates

## Key features

- **Sync-first API** — simple one-liners with no event loop required
- **Async bulk operations** — concurrent fetches with bounded concurrency and rate limiting
- **Typed data models** — frozen dataclasses with a `.raw` passthrough for schema resilience
- **Full CLI** — six commands covering info lookup, download, and bulk metadata fetching
- **Download verification** — SHA-256 checksum checking out of the box
- **Resume support** — bulk operations checkpoint progress so interrupted jobs can restart

## Quick look

**Shell:**
```bash
pypi-librarian info requests
pypi-librarian download flask --dest ./dist
```

**Python:**
```python
from pypi_librarian import Repository

repo = Repository()
project = repo.get_project("requests")
print(project.info.version)   # "2.32.3"
print(project.info.summary)   # "Python HTTP for Humans."
```

## Navigation

| Section | What you will find |
|---|---|
| [Getting Started](getting-started.md) | Installation and first steps |
| [CLI Reference](cli.md) | Every command, argument, and flag |
| [Python API](api.md) | `Repository` and `Downloader` reference |
| [Data Models](models.md) | All typed dataclasses |
| [Bulk Operations](bulk.md) | Concurrent downloads and metadata fetching |
| [Configuration](configuration.md) | Rate limits, concurrency, custom mirrors |
