# Configuration

pypi-librarian has no config file. All settings are passed as constructor arguments or CLI flags.

---

## Custom PyPI mirror

Point `Repository` at any PyPI-compatible index:

```python
from pypi_librarian import Repository

repo = Repository(base_url="https://my-internal-pypi.example.com")
project = repo.get_project("my-private-package")
```

The `base_url` is used as the root for all API calls (`/pypi/<name>/json`, `/simple/`, `/rss/`, etc.).

---

## Concurrency

`max_concurrency` controls the maximum number of simultaneous HTTP requests made by async bulk methods:

```python
repo = Repository(max_concurrency=20)  # default is 10
```

For downloads and metadata fetching, use `DownloadPolicy.max_workers` or `FetchMetadata(max_workers=...)`:

```python
from pypi_librarian.download import DownloadPolicy

policy = DownloadPolicy(max_workers=20)
```

---

## Rate limiting

All bulk operations use a token-bucket rate limiter. The default is **10 requests per second**.

```python
from pypi_librarian.download import DownloadPolicy

# Slow down to 2 req/s to be extra polite
policy = DownloadPolicy(rate_limit=2.0)

# No limit (use with caution)
policy = DownloadPolicy(rate_limit=0)
```

The rate limiter also handles `Retry-After` headers automatically.

From the CLI:

```bash
pypi-librarian download-many --from-file packages.txt --rate 5
```

---

## Distribution types

Control which file types are downloaded:

```python
from pypi_librarian.download import DownloadPolicy

# Wheels only
policy = DownloadPolicy(file_types=["bdist_wheel"])

# Source distributions only
policy = DownloadPolicy(file_types=["sdist"])

# Everything
policy = DownloadPolicy(file_types=["bdist_wheel", "sdist", "bdist_egg"])
```

From the CLI:

```bash
pypi-librarian download requests --types bdist_wheel
pypi-librarian download-many --from-file pkgs.txt --types bdist_wheel,sdist
```

---

## Checksum verification

SHA-256 verification is **on by default**. Disable it only if you have a specific reason:

```python
policy = DownloadPolicy(verify_checksums=False)
```

---

## Logging

pypi-librarian uses the standard `logging` module. The logger name is `pypi_librarian`.

**From Python:**

```python
import logging

logging.basicConfig(level=logging.DEBUG)
# or target just pypi-librarian:
logging.getLogger("pypi_librarian").setLevel(logging.DEBUG)
```

**From the CLI:**

```bash
pypi-librarian --log-level DEBUG info requests
pypi-librarian --log-level INFO download-many --from-file packages.txt
```

Available levels: `DEBUG`, `INFO`, `WARNING` (default), `ERROR`, `CRITICAL`.
