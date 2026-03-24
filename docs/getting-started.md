# Getting Started

## Requirements

- Python 3.10 or later
- Works on Linux, macOS, and Windows

## Installation

Install from PyPI:

```bash
pip install pypi_librarian
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add pypi_librarian
```

## Verify the install

```bash
pypi-librarian --version
```

## First steps — CLI

Look up a package:

```bash
pypi-librarian info httpx
```

List all released versions:

```bash
pypi-librarian versions httpx
```

See the newest packages on PyPI:

```bash
pypi-librarian latest
```

Download the latest wheel and source distribution:

```bash
pypi-librarian download httpx --dest ./downloads
```

## First steps — Python

```python
from pypi_librarian import Repository

repo = Repository()

# Fetch all metadata for a package
project = repo.get_project("httpx")

print(project.info.name)          # "httpx"
print(project.info.version)       # latest version string
print(project.info.summary)       # one-line description
print(project.info.license)       # license identifier
print(project.info.requires_python)  # e.g. ">=3.8"

# List every released version
for release in project.releases:
    print(release.version, len(release.files), "file(s)")
```

## What is NOT included

pypi-librarian intentionally does not:

- **Install** packages into your environment — use `pip` or `uv` for that
- **Upload** packages to PyPI — use `twine` for that
- **Mirror** PyPI at scale — use `bandersnatch` for that
- **Search** PyPI by keyword — PyPI has no public search API

## Next steps

- See [CLI Reference](cli.md) for all available commands
- See [Python API](api.md) to use pypi-librarian as a library
- See [Bulk Operations](bulk.md) for concurrent downloads and metadata fetching
