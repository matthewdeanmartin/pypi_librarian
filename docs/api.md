# Python API

The primary entry point is the `Repository` class. Import it from the top-level package:

```python
from pypi_librarian import Repository
```

---

## `Repository`

```python
class Repository:
    def __init__(
        self,
        base_url: str = "https://pypi.org",
        max_concurrency: int = 10,
    ): ...
```

**Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `base_url` | `"https://pypi.org"` | Base URL of the PyPI-compatible index to query |
| `max_concurrency` | `10` | Maximum concurrent requests used by async bulk methods |

---

### Single-object queries (synchronous)

These methods make one HTTP request and return immediately. No event loop required.

#### `get_project`

```python
def get_project(self, name: str) -> Project
```

Fetch all metadata for a package across every released version.

Raises `ValueError` if the package is not found.

```python
repo = Repository()
project = repo.get_project("requests")
print(project.info.version)           # latest version
print(len(project.releases))          # number of releases
```

#### `get_package`

```python
def get_package(self, name: str, version: str) -> Package
```

Fetch metadata for a specific (name, version) pair.

```python
pkg = repo.get_package("requests", "2.31.0")
print(pkg.info.requires_python)
```

#### `get_user`

```python
def get_user(self, name: str) -> User
```

Fetch a PyPI user's profile and the list of packages they maintain.

```python
user = repo.get_user("kennethreitz")
print(user.packages)   # list of package name strings
```

#### `get_all_package_names`

```python
def get_all_package_names(self) -> Iterator[str]
```

Lazily yield every package name on the index (roughly 600 000+ on PyPI). Parses the `/simple/` HTML index.

```python
for name in repo.get_all_package_names():
    print(name)
```

#### `project_names_by_user`

```python
def project_names_by_user(self, name: str) -> list[str]
```

Return the list of package names maintained by a user without fetching full metadata.

#### `projects_by_user`

```python
def projects_by_user(self, name: str) -> list[Project]
```

Return full `Project` objects for every package maintained by a user. Makes one request per package — use sparingly for prolific maintainers.

---

### RSS feeds (synchronous)

#### `newest_packages`

```python
def newest_packages(self, count: int = 40) -> list[NewPackage]
```

Return the most recently *created* packages from the PyPI RSS feed.

#### `latest_updates`

```python
def latest_updates(self, count: int = 40) -> list[NewRelease]
```

Return the most recently *updated* packages from the PyPI RSS feed.

---

### Bulk queries (synchronous wrappers)

These methods run async operations in a thread and block until complete.

#### `get_many_projects`

```python
def get_many_projects(self, names: list[str]) -> list[Project]
```

Fetch `Project` objects for multiple packages concurrently. Respects `max_concurrency`.

```python
projects = repo.get_many_projects(["requests", "flask", "httpx"])
for p in projects:
    print(p.info.name, p.info.version)
```

#### `get_many_packages`

```python
def get_many_packages(self, items: list[tuple[str, str]]) -> list[Package]
```

Fetch `Package` objects for multiple (name, version) pairs concurrently.

```python
items = [("requests", "2.31.0"), ("flask", "3.0.0")]
packages = repo.get_many_packages(items)
```

---

### Bulk queries (async)

Use these directly when you are already in an async context.

#### `get_many_projects_async`

```python
async def get_many_projects_async(self, names: list[str]) -> list[Project]
```

#### `get_many_packages_async`

```python
async def get_many_packages_async(
    self, items: list[tuple[str, str]]
) -> list[Package]
```

#### `get_all_package_names_async`

```python
async def get_all_package_names_async(self) -> AsyncIterator[str]
```

---

### Downloads (via `Repository`)

Convenience wrappers that delegate to `Downloader`.

#### `download`

```python
def download(
    self,
    name: str,
    version: str | None = None,
    dest_dir: str | Path = ".",
    policy: DownloadPolicy | None = None,
) -> DownloadResult
```

Download distribution files for one package synchronously.

#### `download_many`

```python
def download_many(
    self,
    names: list[str],
    dest_dir: str | Path = ".",
    policy: DownloadPolicy | None = None,
    resume: bool = False,
) -> list[DownloadResult]
```

Download distribution files for multiple packages concurrently.

---

### Metadata fetching (via `Repository`)

#### `fetch_metadata`

```python
def fetch_metadata(
    self,
    dest_dir: str | Path = "metadata",
    names: list[str] | None = None,
    limit: int = 0,
) -> int
```

Fetch raw JSON metadata for many packages and write one `.json` file per package. Returns the number of packages fetched.

---

## `run_async` utility

When you need to call an async method from synchronous code and do not want to manage an event loop yourself:

```python
from pypi_librarian.utils import run_async

results = run_async(repo.get_many_projects_async(["requests", "flask"]))
```

- Uses `asyncio.run()` when no event loop is running
- Falls back to a thread pool when called from inside a running loop (e.g., a Jupyter notebook)

---

## Calling from async code

pypi-librarian works naturally inside existing async applications:

```python
import asyncio
from pypi_librarian import Repository

async def main():
    repo = Repository(max_concurrency=20)
    projects = await repo.get_many_projects_async(["requests", "flask", "httpx"])
    for p in projects:
        print(p.info.name, p.info.version)

asyncio.run(main())
```

---

## Error handling

```python
from pypi_librarian import Repository

repo = Repository()

try:
    project = repo.get_project("this-package-does-not-exist-xyz")
except ValueError as exc:
    print("Not found:", exc)
```

Network errors raise standard `httpx` exceptions (`httpx.HTTPError` and its subclasses). Wrap bulk calls in a `try/except` if you need to handle transient failures.
