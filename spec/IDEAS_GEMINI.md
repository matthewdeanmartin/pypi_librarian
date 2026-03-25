# Feature Ideas for pypi-librarian

This document tracks potential features and enhancements to expand the capabilities of `pypi-librarian`.

## 1. Metadata & Analysis
- **Dependency Tree Visualization**: Add a command to recursively fetch and display a package's dependency tree (e.g., `pypi-librarian tree requests`).
- **Package Comparison**: Support side-by-side comparison of multiple packages (e.g., `pypi-librarian compare requests httpx urllib3`) to compare health scores, download counts, and metadata.
- **Advanced Health Metrics**:
  - **Bus Factor**: Estimate "bus factor" based on GitHub contributor activity.
  - **Issue Resolution Time**: Calculate the average time to close issues/PRs from GitHub data.
  - **CWE/Vulnerability Integration**: Show known vulnerabilities (via OSV.dev or similar) in the `enrich` output.
- **License Compliance Auditor**: Scan a package and all its dependencies to identify potential license conflicts or "copyleft" risks.

## 2. CLI & UX Improvements
- **Interactive TUI**: A terminal UI (built with `rich` or `textual`) for browsing PyPI, searching, and viewing package details without repeated CLI calls.
- **Export Formats**: Add `--format [json|csv|md|html]` to `info` and `enrich` commands for easier integration with reports and CI/CD pipelines.
- **Shell Autocompletion**: Generate completion scripts for `bash`, `zsh`, and `fish`.
- **Progressive Search**: Implement a local fuzzy search over a cached list of all PyPI package names.

## 3. Automation & Monitoring
- **Watchdog / Notification Mode**: A background worker or periodic task that monitors specific packages for new releases and sends notifications (e.g., via Slack, Discord, or Email).
- **Batch Download Hooks**: Allow users to specify a script/command to run after a successful package download (e.g., auto-scanning for malware).
- **GitHub Action**: Create a dedicated GitHub Action for `pypi-librarian` to check dependencies for health/staleness in CI.

## 4. Performance & Infrastructure
- **Persistent Local Cache**: Implement a SQLite-backed cache for metadata to reduce redundant network calls and improve speed for repeated lookups.
- **Delta Metadata Updates**: Use PyPI's RSS or Serial IDs to incrementally update the local metadata cache rather than full re-fetches.
- **Proxy Support & Mirrors**: Formalize support for private PyPI mirrors (Artifactory, Nexus) and authenticated proxies.

## 5. Security
- **Signature Verification**: Automatically verify PGP/GPG signatures or PEP 740 (Sigstore) attestations during download.
- **Malware Heuristics**: Basic static analysis of downloaded packages to look for common malware patterns (e.g., obfuscated code, suspicious network calls in `setup.py`).
- **Verified Maintainers**: Highlight "Verified" status on PyPI or 2FA-enabled maintainers if that data becomes available in the API.
