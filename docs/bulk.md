# Bulk Operations

pypi-librarian provides two bulk-operation subsystems: **Downloader** for downloading distribution files, and **FetchMetadata** for downloading raw JSON metadata. Both run asynchronously under the hood with a synchronous wrapper for convenience.

---

## Downloading distribution files

### Via `Repository` (simplest)

```python
from pypi_librarian import Repository

repo = Repository()

# Download one package
result = repo.download("requests", dest_dir="./dist")
print(result.files)     # list of saved file paths
print(result.errors)    # list of error messages (empty = all good)

# Download several packages at once
results = repo.download_many(
    ["requests", "flask", "httpx"],
    dest_dir="./dist",
)
for r in results:
    print(r.name, "->", r.files)
```

### Via `Downloader` directly

Use `Downloader` when you need fine-grained control over policy.

```python
from pypi_librarian.download import Downloader, DownloadPolicy

policy = DownloadPolicy(
    file_types=["bdist_wheel"],   # wheels only
    max_workers=5,
    rate_limit=5.0,               # 5 requests/sec
    verify_checksums=True,
)

dl = Downloader(dest_dir="./dist", policy=policy)

# Synchronous — blocks until done
result = dl.download_one_sync("requests")
results = dl.download_many_sync(["requests", "flask", "httpx"])
```

### Resume interrupted downloads

```python
# First run (may be interrupted)
dl.go_or_resume_sync(["requests", "flask", "httpx", ...])

# Re-run — already-completed packages are skipped
dl.go_or_resume_sync(["requests", "flask", "httpx", ...])
```

Or from the CLI:

```bash
pypi-librarian download-many --from-file packages.txt --dest ./dist
# interrupted...
pypi-librarian download-many --from-file packages.txt --dest ./dist --resume
```

### Async download

```python
import asyncio
from pypi_librarian.download import Downloader

async def main():
    dl = Downloader(dest_dir="./dist")
    result = await dl.download_one("requests")
    results = await dl.download_many(["requests", "flask"])

asyncio.run(main())
```

---

## Fetching JSON metadata

`FetchMetadata` downloads the raw PyPI JSON for each package and writes one `.json` file per package. This is useful for offline analysis or building a local index.

### Via `Repository`

```python
repo = Repository()

# Fetch for a specific list
count = repo.fetch_metadata(dest_dir="./metadata", names=["requests", "flask"])
print(f"Fetched {count} packages")

# Fetch everything on PyPI (slow — ~600k packages)
count = repo.fetch_metadata(dest_dir="./metadata")
```

### Via `FetchMetadata` directly

```python
from pypi_librarian.fetch_metadata import FetchMetadata

fm = FetchMetadata(
    dest_dir="./metadata",
    limit=0,           # 0 = no limit
    max_workers=10,
    rate_limit=10.0,
)

# Sync
count = fm.run(names=None)   # None = all packages on PyPI

# Async
import asyncio
count = asyncio.run(fm.run_async(names=None))
```

### Resume behaviour

Re-running `FetchMetadata` (or `fetch-metadata` from the CLI) is safe: any package whose `.json` file already exists is skipped automatically. You do not need a `--resume` flag — just rerun the command.

---

## Rate limiting

All bulk operations respect a configurable rate limit expressed as **requests per second**. The default is `10` requests/sec, which is polite for PyPI's public API.

```python
policy = DownloadPolicy(rate_limit=5.0)   # 5 req/s
```

Set `rate_limit=0` to disable rate limiting entirely (use with caution).

The rate limiter also honours `Retry-After` headers from PyPI, so it automatically backs off when the server asks it to.

---

## Concurrency

Both `Downloader` and `FetchMetadata` bound concurrency via `max_workers` (default `10`). Increase this for faster bulk operations on a fast connection; decrease it if you are hitting rate limits or running on a slow link.

```python
dl = Downloader(dest_dir="./dist", policy=DownloadPolicy(max_workers=20))
```

---

## Checksum verification

Downloads are verified against the SHA-256 digest published by PyPI. If verification fails, `DownloadResult.checksum_ok` is `False` and the failure is recorded in `DownloadResult.errors`.

Disable verification (not recommended):

```python
policy = DownloadPolicy(verify_checksums=False)
```

---

## Working with results

```python
results = repo.download_many(["requests", "flask", "httpx"], dest_dir="./dist")

ok = [r for r in results if not r.errors]
failed = [r for r in results if r.errors]

print(f"{len(ok)} succeeded, {len(failed)} failed")
for r in failed:
    print(r.name, r.errors)
```
