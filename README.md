pypi_librarian
--------------

A more generic library for dowlonading packages from pypi. 

How this relates to other tools that download things from pypi:
- bandersnatch - too focused on being a mirror for pypi
- pip - too focused on package installation
- twine - too focused on package upload
- pipenv - too focused on package installation
- requests - unaware of any specific feature of pypi/warehouse
- pypi_xmlrpc - only uses the xmlrpc endpoints, which are to be deprecated some day.

Specific Scenarios
----
Let's say you want to download all the gzip/zip files for the latest version of your app and put them in a folder so you can do static code analysis on your dependencies. 

Let's say you are writing a linting tool and would like to test it on a large number of real world code bases.

Monitoring PyPi for certain events (new packages, etc.)

Schema
----
**Repository have projects.** These projects can be searched, downloaded in bulk and have various change notification strategies for mirrors

**Projects have maintainers and releases.** One of these releases is the main, most recent release that people care about. The rest are history. Pypi itself doesn't provide change notification, nor download stats. This is now provided by third party services.

**Releases have a package.** The package is a compressed file, either gz, zip or wheel which has some meta data in it as a file, PKG_INFO and more. Dependencies could be in `pyproject.toml`, legacy packaging files, or nowhere.


Existing Solutions
---
[Yolk](https://pypi.org/project/yolk3k/) Command line, queries package metadata

[Pip](https://pypi.org/project/pip/) - Has some search & meta data functionality. Explicitly says that it should not be used as library but only as shell command.

[qypi](https://pypi.org/project/qypi/) - strictly fetches meta data. Outputs json.

Parsing the setup.py/PKG_INFO files
-----
- [pkginfo](https://pypi.org/project/pkginfo/) - attempts to read PKG_INFO if it can find it. I couldn't get it to work.
- [pkg_info](https://pypi.org/project/pkg_info/) - appears to be a tiny script that queries pypi for the same

similar things
- [bento](https://pypi.org/project/bento/) - a tool for making pip compatible packages, using a yaml-like bento file instead of a setup.py file
- [poetry](https://python-poetry.org/docs/pyproject/) - creates packages, uses a `pyproject.toml` file
- tools built around `pyproject.toml` make it easier to keep project metadata and dependency definitions in one place.


Package Statitics
----
[Libraries.io](https://libraries.io/api) Numerous REST enpoints, no python client that I can find yet.

[pypistats](https://github.com/hugovk/pypistats) output version info in many formats. Serves data from https://pypistats.org/api/ - which is from the official PyPi "big table" records.

[pkginfo](https://pypi.org/project/pkginfo/) Parses pkg info file found in package gz/zip/whl files


Pypi mirrors
------------
Bandersnatch

[Dumb-pypi](https://github.com/chriskuehl/dumb-pypi)


Commercial Package Repos
---
I plan to implement support for pypi & compatible mirrors first.

- packagecloud.io
- gemfury

## Development

This repository now uses `uv` for environment and dependency management, `pyproject.toml` for package metadata and tool configuration, Hatch for builds, and `Makefile` targets for common workflows.

Common commands:

- `uv sync --group dev`
- `make format`
- `make lint`
- `make test`
- `make build`

## Project Links

- [GitHub](https://github.com/matthewdeanmartin/pypi_librarian)
- [PyPI](https://pypi.org/project/pypi-librarian/)
- [Bug Tracker](https://github.com/matthewdeanmartin/pypi_librarian/issues)


## Python 3.15 verification (2026-10-04)

The earlier HTTPX bound is superseded by the HTTPX2 verification below.

Stable locks were refreshed with `uv lock --upgrade`. Dependency verification uses fresh environments and published wheels only; no source builds. Full developer tools still have wheel blockers (linkcheckmd or PyYAML); passing unit tests do not certify the full developer group. Evidence and details: `C:/github/python315_batch5_2026-10-04.md`. Human operators review and file any upstream bugs.


## HTTPX2 verification (2026-10-04)

Sync/async clients use HTTPX2; tests use httpx2-pytest and httpx2_mock. All 179 unit tests pass / 18 integration deselected in RC3 stable/pre and 3.14.7, plus installed-wheel startup. Public client/response/exception types are now HTTPX2 types. Reconcile local 0.1.6 with PyPI 0.1.9 before publishing.

Dependency installs require published wheels; no native builds or GitHub jobs. Experimental mode allows prereleases but the successful HTTPX2 test environments selected stable packages. Locks were upgraded with `uv lock --upgrade`. Changes are local; human operators decide publishing and upstream reports.
