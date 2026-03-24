# Data Models

All models are **frozen dataclasses** (immutable after creation). Every model carries a `raw` field containing the original API response dict, which lets you access fields that pypi-librarian does not yet model explicitly.

Import models from:

```python
from pypi_librarian.models import (
    Project,
    Package,
    Release,
    ReleaseFile,
    ProjectInfo,
    User,
    NewPackage,
    NewRelease,
    DownloadPolicy,
    DownloadResult,
)
```

---

## `Project`

A package across all its versions.

```python
@dataclass
class Project:
    name: str                        # canonical package name
    info: ProjectInfo                # metadata from the latest version
    releases: list[Release]          # every released version
    latest_files: list[ReleaseFile]  # distribution files for the latest version
    raw: dict[str, Any]              # original JSON from PyPI
```

**Example:**

```python
project = repo.get_project("requests")
project.name                          # "requests"
project.info.version                  # "2.32.3"
project.info.summary                  # "Python HTTP for Humans."
len(project.releases)                 # total number of versions
project.latest_files[0].filename     # e.g. "requests-2.32.3-py3-none-any.whl"
```

---

## `ProjectInfo`

Metadata from one version (usually the latest). Lives at `project.info` or `package.info`.

```python
@dataclass(frozen=True)
class ProjectInfo:
    name: str
    version: str
    summary: str | None
    author: str | None
    author_email: str | None
    maintainer: str | None
    maintainer_email: str | None
    license: str | None
    home_page: str | None
    project_url: str | None          # Homepage from project_urls
    requires_python: str | None      # e.g. ">=3.8"
    classifiers: tuple[str, ...]     # immutable tuple
    keywords: str | None
    description: str | None          # long-form description (often a README)
    description_content_type: str | None  # e.g. "text/markdown"
    requires_dist: tuple[str, ...]   # dependency specifiers; immutable tuple
    yanked: bool
    yanked_reason: str | None
    raw: dict[str, Any]
```

---

## `Release`

One version of a package with its distribution files.

```python
@dataclass
class Release:
    version: str              # e.g. "2.28.1"
    files: list[ReleaseFile]  # all distribution files for this version
    raw: dict[str, Any]
```

**Example:**

```python
for release in project.releases:
    wheels = [f for f in release.files if f.packagetype == "bdist_wheel"]
    print(release.version, len(wheels), "wheel(s)")
```

---

## `ReleaseFile`

One distribution file (a wheel, sdist, or other artifact).

```python
@dataclass(frozen=True)
class ReleaseFile:
    filename: str              # e.g. "requests-2.28.1-py3-none-any.whl"
    url: str                   # direct download URL
    size: int                  # file size in bytes
    md5_digest: str            # MD5 digest (deprecated; prefer sha256)
    sha256_digest: str         # SHA-256 digest for verification
    packagetype: str           # "bdist_wheel", "sdist", etc.
    python_version: str        # "py3", "cp311", "source", etc.
    requires_python: str | None
    upload_time: str           # ISO 8601 timestamp
    yanked: bool
    yanked_reason: str | None
    raw: dict[str, Any]
```

**Common `packagetype` values:**

| Value | Meaning |
|---|---|
| `bdist_wheel` | Built wheel (`.whl`) |
| `sdist` | Source distribution (`.tar.gz` or `.zip`) |
| `bdist_egg` | Legacy egg format |
| `bdist_wininst` | Legacy Windows installer |

---

## `Package`

A specific (name, version) combination with full metadata and file list.

```python
@dataclass
class Package:
    name: str
    version: str
    info: ProjectInfo         # metadata for this exact version
    files: list[ReleaseFile]  # distribution files for this version
    raw: dict[str, Any]
```

---

## `User`

A PyPI user and the packages they maintain.

```python
@dataclass
class User:
    name: str            # PyPI username
    packages: list[str]  # package names (not full objects)
    raw: dict[str, Any]
```

---

## `NewPackage`

An entry from the PyPI "new packages" RSS feed.

```python
@dataclass(frozen=True)
class NewPackage:
    title: str        # e.g. "my-package 1.0.0"
    link: str         # URL to the PyPI project page
    description: str  # short description
    published: str    # RFC 2822 date string
    raw: dict[str, Any]
```

---

## `NewRelease`

An entry from the PyPI "latest updates" RSS feed.

```python
@dataclass(frozen=True)
class NewRelease:
    title: str
    link: str
    description: str
    published: str    # RFC 2822 date string
    raw: dict[str, Any]
```

---

## `DownloadPolicy`

Controls how downloads are executed.

```python
@dataclass(frozen=True)
class DownloadPolicy:
    file_types: list[str] = field(default_factory=lambda: ["bdist_wheel", "sdist"])
    max_workers: int = 10          # concurrent download threads
    rate_limit: float = 10.0       # max HTTP requests per second (0 = unlimited)
    verify_checksums: bool = True   # verify SHA-256 after each download
```

---

## `DownloadResult`

The outcome of downloading one package.

```python
@dataclass
class DownloadResult:
    name: str              # package name
    version: str           # version that was downloaded
    files: list[str]       # paths to successfully downloaded files
    errors: list[str]      # error messages for any failures
    skipped: list[str]     # filenames that were skipped (wrong type, already exists, etc.)
    checksum_ok: bool      # True if all SHA-256 checks passed
```

---

## Accessing unlisted fields with `.raw`

PyPI occasionally adds new fields to its JSON responses. The `.raw` dict always contains the complete original response so you can access anything not yet modelled:

```python
project = repo.get_project("requests")

# A field pypi-librarian doesn't model yet:
yanked_by = project.info.raw.get("yanked_by")
```
