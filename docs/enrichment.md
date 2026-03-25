# Data Enrichment

pypi-librarian can enrich package metadata with data from external sources: download statistics from [pypistats.org](https://pypistats.org) and repository metadata from GitHub.

---

## Download statistics

Fetch download counts from pypistats.org:

```python
from pypi_librarian import Repository

repo = Repository()
stats = repo.get_download_stats("requests")

if stats:
    print(stats.last_day)    # int
    print(stats.last_week)   # int
    print(stats.last_month)  # int
```

Returns `None` if the package is unknown to pypistats. Stats are updated daily on pypistats.org's side.

### Direct usage

```python
from pypi_librarian.pypistats import fetch_download_stats

stats = fetch_download_stats("flask")
```

### `DownloadStats` fields

| Field | Type | Description |
|---|---|---|
| `package` | `str` | Package name |
| `last_day` | `int` | Downloads in the last day |
| `last_week` | `int` | Downloads in the last week |
| `last_month` | `int` | Downloads in the last month |
| `raw` | `dict` | Original API response |

---

## GitHub enrichment

Fetch public repository metadata for a package. pypi-librarian automatically extracts the GitHub URL from the package's PyPI metadata.

```python
repo = Repository()
github = repo.get_github_info("requests")

if github:
    print(github.stars)        # int
    print(github.forks)        # int
    print(github.open_issues)  # int
    print(github.last_push)    # ISO 8601 string or None
    print(github.archived)     # bool
```

Returns `None` if the package has no GitHub URL, if the repo is not found, or if the request is rate-limited.

### Authentication

Unauthenticated GitHub API requests are rate-limited to 60 per hour. To increase this to 5000/hr, provide a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens):

```python
# Via environment variable (recommended)
# export GITHUB_TOKEN=ghp_...

# Or pass directly
github = repo.get_github_info("requests", token="ghp_...")
```

### Direct usage

```python
from pypi_librarian.github import fetch_github_info, fetch_github_info_for_project

# If you already have the owner/repo:
info = fetch_github_info("psf", "requests")

# If you only have PyPI project URLs:
info = fetch_github_info_for_project(
    project_url="https://github.com/psf/requests",
    home_page=None,
)
```

### `GitHubInfo` fields

| Field | Type | Description |
|---|---|---|
| `owner` | `str` | GitHub user or org |
| `repo` | `str` | Repository name |
| `stars` | `int` | Star count |
| `forks` | `int` | Fork count |
| `open_issues` | `int` | Open issues count |
| `last_push` | `str \| None` | ISO 8601 timestamp of last push |
| `description` | `str \| None` | Repository description |
| `archived` | `bool` | Whether the repo is archived |
| `raw` | `dict` | Original GitHub API response |

---

## Health scoring

Get a single 0–1 score summarising a package's health and activity:

```python
repo = Repository()
health = repo.health_score("requests")

print(health.score)    # float, e.g. 0.9375
print(health.notes)    # list of issues found, e.g. ["No license declared"]
print(health.components)  # per-component scores dict
```

The score combines:

| Component | Weight | What it measures |
|---|---|---|
| `has_summary` | 0.10 | `summary` is non-empty |
| `has_classifiers` | 0.10 | `classifiers` is non-empty |
| `has_license` | 0.10 | `license` is non-empty |
| `requires_python_recent` | 0.15 | `requires_python` targets Python 3.8+ |
| `not_yanked` | 0.10 | Latest version is not yanked |
| `release_cadence` | 0.20 | Has had a release in the past 2 years |
| `download_trend` | 0.15 | Last-month downloads > 0 (pypistats) |
| `github_active` | 0.10 | Last GitHub push within 2 years |

Components for which data is unavailable are excluded from the denominator, so the score is always normalised to [0, 1] based on what could actually be measured.

### Controlling what gets fetched

```python
# Skip pypistats (faster, no download component)
health = repo.health_score("requests", include_downloads=False)

# Skip GitHub (no GITHUB_TOKEN needed)
health = repo.health_score("requests", include_github=False)

# Both — score from PyPI metadata only
health = repo.health_score("requests", include_downloads=False, include_github=False)
```

### Direct usage

```python
from pypi_librarian.health import score_project

health = score_project(
    info=project.info,
    releases_upload_times=[f.upload_time for r in project.releases for f in r.files],
    stats=stats,    # DownloadStats or None
    github=github,  # GitHubInfo or None
)
```

---

## CLI — `enrich` command

```bash
pypi-librarian enrich requests
```

Shows downloads, GitHub info, and health score for a package.

**Options:**

| Option | Default | Description |
|---|---|---|
| `--with SOURCE,...` | `downloads,github,health` | Comma-separated sources to include |
| `--github-token TOKEN` | env `GITHUB_TOKEN` | GitHub personal-access token |

**Examples:**

```bash
# Full enrichment
pypi-librarian enrich flask

# Downloads only
pypi-librarian enrich flask --with downloads

# Health score only (no external calls except PyPI)
pypi-librarian enrich flask --with health

# With GitHub auth
pypi-librarian enrich flask --github-token ghp_abc123
```
