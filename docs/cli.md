# CLI Reference

The CLI is available as `pypi-librarian` after installation.

```
usage: pypi-librarian [-h] [--version] [--log-level LEVEL] <command> ...
```

## Global options

| Option | Values | Default | Description |
|---|---|---|---|
| `--version` | — | — | Print version and exit |
| `--log-level` | `DEBUG` `INFO` `WARNING` `ERROR` `CRITICAL` | `WARNING` | Set log verbosity |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Package not found or validation error |
| `2` | Network error or unexpected exception |

---

## `info` — look up a package

Print metadata for the latest version of a package.

```bash
pypi-librarian info <package>
```

**Arguments:**

| Argument | Description |
|---|---|
| `package` | PyPI package name (case-insensitive) |

**Output includes:** name, version, summary, author, license, Python requirement, classifiers, and dependencies.

**Examples:**

```bash
pypi-librarian info requests
pypi-librarian info "Pillow"
```

---

## `versions` — list all versions

List every released version of a package with its file count.

```bash
pypi-librarian versions <package>
```

**Arguments:**

| Argument | Description |
|---|---|
| `package` | PyPI package name |

**Example:**

```bash
pypi-librarian versions flask
```

---

## `latest` — newest packages on PyPI

Show the most recently published packages from the PyPI RSS feed.

```bash
pypi-librarian latest
```

No arguments. Returns up to 40 entries by default.

---

## `download` — download a package

Download distribution files for a single package.

```bash
pypi-librarian download <package> [options]
```

**Arguments:**

| Argument | Description |
|---|---|
| `package` | PyPI package name |

**Options:**

| Option | Default | Description |
|---|---|---|
| `--version VERSION` | latest | Specific version to download |
| `--dest DIR` | `.` (current directory) | Directory to write files into |
| `--types TYPE,...` | `bdist_wheel,sdist` | Comma-separated list of distribution types to fetch |

**Distribution type values:** `bdist_wheel`, `sdist`, `bdist_egg`, `bdist_wininst`

**Examples:**

```bash
# Download latest wheel + sdist into ./dist
pypi-librarian download requests --dest ./dist

# Download only the wheel for a specific version
pypi-librarian download requests --version 2.31.0 --types bdist_wheel

# Download the source distribution only
pypi-librarian download flask --types sdist --dest /tmp/pkgs
```

---

## `download-many` — bulk download

Download distribution files for multiple packages concurrently.

```bash
pypi-librarian download-many --from-file FILE [options]
```

**Required options:**

| Option | Description |
|---|---|
| `--from-file FILE` | Path to a plain-text file with one package name per line |

**Optional options:**

| Option | Default | Description |
|---|---|---|
| `--dest DIR` | `.` | Directory to write files into |
| `--workers N` | `10` | Number of concurrent download workers |
| `--rate R` | `10` | Maximum requests per second (`0` = unlimited) |
| `--resume` | off | Resume an interrupted download using the checkpoint file |
| `--types TYPE,...` | `bdist_wheel,sdist` | Distribution types to fetch |

**Package list file format:**

```
requests
flask
httpx
# blank lines and lines starting with # are ignored
```

**Examples:**

```bash
# Download wheels + sdists for every package in packages.txt
pypi-librarian download-many --from-file packages.txt --dest ./dist

# Resume an interrupted run
pypi-librarian download-many --from-file packages.txt --dest ./dist --resume

# Limit to 5 concurrent workers and 5 requests/sec
pypi-librarian download-many --from-file packages.txt --workers 5 --rate 5
```

**Resume behaviour:** The tool writes a checkpoint file (NDJSON) alongside the destination directory. When `--resume` is passed, packages that already have a completed entry in the checkpoint are skipped.

---

## `fetch-metadata` — bulk metadata download

Download raw JSON metadata for many packages and save one `.json` file per package.

```bash
pypi-librarian fetch-metadata [options]
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--dest DIR` | `metadata` | Directory to write `.json` files into |
| `--limit N` | `0` (all) | Stop after fetching N packages |
| `--from-file FILE` | — | Fetch only the packages listed in FILE; if omitted, fetches all packages on PyPI |
| `--workers N` | `10` | Concurrent fetch workers |
| `--rate R` | `10` | Maximum requests per second |

**Examples:**

```bash
# Fetch metadata for every package on PyPI (slow — ~600k packages)
pypi-librarian fetch-metadata --dest ./metadata

# Fetch a specific list
pypi-librarian fetch-metadata --from-file packages.txt --dest ./metadata

# Test run: first 100 packages only
pypi-librarian fetch-metadata --limit 100 --dest ./metadata-sample
```

**Resume behaviour:** If a `.json` file already exists for a package it is skipped automatically, so re-running the command resumes where it left off.
