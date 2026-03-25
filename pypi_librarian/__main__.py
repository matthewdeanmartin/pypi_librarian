# coding=utf-8
"""
pypi-librarian — CLI for querying PyPI metadata and downloading packages.

Usage examples::

    pypi-librarian info requests
    pypi-librarian versions requests
    pypi-librarian latest
    pypi-librarian download requests --dest ./packages
    pypi-librarian download-many --from-file packages.txt --dest ./packages
    pypi-librarian fetch-metadata --dest ./metadata --limit 100
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from pypi_librarian._version import __version__
from pypi_librarian.class_repo import Repository
from pypi_librarian.download import DownloadPolicy, Downloader
from pypi_librarian.fetch_metadata import FetchMetadata

__all__ = ["main"]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pypi-librarian",
        description="Query PyPI package metadata and download distributions.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        metavar="LEVEL",
        help="Logging verbosity (default: WARNING).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # info
    info_p = sub.add_parser("info", help="Print metadata for a package.")
    info_p.add_argument("package", help="Package name on PyPI.")

    # versions
    ver_p = sub.add_parser("versions", help="List all versions of a package.")
    ver_p.add_argument("package", help="Package name on PyPI.")

    # latest
    sub.add_parser("latest", help="Show newest packages from the RSS feed.")

    # download
    dl_p = sub.add_parser("download", help="Download distribution files for a package.")
    dl_p.add_argument("package", help="Package name on PyPI.")
    dl_p.add_argument("--version", "-V", dest="pkg_version", default=None,
                       help="Specific version to download (default: latest).")
    dl_p.add_argument("--dest", default=".", help="Destination directory (default: .).")
    dl_p.add_argument("--types", default="bdist_wheel,sdist",
                       help="Comma-separated file types (default: bdist_wheel,sdist).")

    # download-many
    dm_p = sub.add_parser("download-many", help="Download files for multiple packages.")
    dm_p.add_argument("--from-file", required=True, dest="from_file",
                       help="Text file with one package name per line.")
    dm_p.add_argument("--dest", default=".", help="Destination directory (default: .).")
    dm_p.add_argument("--workers", type=int, default=10,
                       help="Max concurrent downloads (default: 10).")
    dm_p.add_argument("--rate", type=float, default=10.0,
                       help="Max requests per second (default: 10).")
    dm_p.add_argument("--resume", action="store_true",
                       help="Resume from checkpoint, skip already-downloaded packages.")
    dm_p.add_argument("--types", default="bdist_wheel,sdist",
                       help="Comma-separated file types (default: bdist_wheel,sdist).")

    # fetch-metadata
    fm_p = sub.add_parser("fetch-metadata",
                           help="Fetch JSON metadata for packages into a directory.")
    fm_p.add_argument("--dest", default="metadata",
                       help="Destination directory (default: metadata).")
    fm_p.add_argument("--limit", type=int, default=0,
                       help="Max packages to fetch (default: 0 = all).")
    fm_p.add_argument("--workers", type=int, default=10,
                       help="Max concurrent requests (default: 10).")
    fm_p.add_argument("--rate", type=float, default=10.0,
                       help="Max requests per second (default: 10).")
    fm_p.add_argument("--from-file", dest="from_file", default=None,
                       help="Text file with package names (default: use /simple/).")

    # enrich
    enrich_p = sub.add_parser("enrich", help="Show enrichment data for a package.")
    enrich_p.add_argument("package", help="Package name on PyPI.")
    enrich_p.add_argument(
        "--with",
        dest="sources",
        default="downloads,github,health",
        help="Comma-separated enrichment sources: downloads, github, health "
             "(default: downloads,github,health).",
    )
    enrich_p.add_argument(
        "--github-token",
        dest="github_token",
        default=None,
        help="GitHub personal-access token (overrides GITHUB_TOKEN env var).",
    )

    return parser


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def _cmd_info(args: argparse.Namespace, repo: Repository) -> int:
    try:
        project = repo.get_project(args.package)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.debug("Unexpected error", exc_info=True)
        print(f"Network error: {exc}", file=sys.stderr)
        return 2

    info = project.info
    print(f"Name:           {info.name}")
    print(f"Version:        {info.version}")
    print(f"Summary:        {info.summary or '(none)'}")
    print(f"Author:         {info.author or '(none)'}")
    print(f"Author email:   {info.author_email or '(none)'}")
    print(f"License:        {info.license or '(none)'}")
    print(f"Requires Python:{info.requires_python or '(none)'}")
    print(f"Project URL:    {info.project_url or info.home_page or '(none)'}")
    if info.classifiers:
        print("Classifiers:")
        for c in info.classifiers:
            print(f"  {c}")
    if info.requires_dist:
        print("Requires:")
        for dep in info.requires_dist:
            print(f"  {dep}")
    if info.yanked:
        print(f"YANKED: {info.yanked_reason or '(no reason given)'}")
    return 0


def _cmd_versions(args: argparse.Namespace, repo: Repository) -> int:
    try:
        project = repo.get_project(args.package)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.debug("Unexpected error", exc_info=True)
        print(f"Network error: {exc}", file=sys.stderr)
        return 2

    for release in project.releases:
        file_count = len(release.files)
        print(f"{release.version}  ({file_count} file{'s' if file_count != 1 else ''})")
    return 0


def _cmd_latest(_args: argparse.Namespace, repo: Repository) -> int:
    try:
        packages = repo.newest_packages()
    except Exception as exc:
        logger.debug("Unexpected error", exc_info=True)
        print(f"Network error: {exc}", file=sys.stderr)
        return 2

    for pkg in packages:
        print(f"{pkg.title}")
        print(f"  {pkg.link}")
        if pkg.description:
            print(f"  {pkg.description}")
    return 0


def _cmd_download(args: argparse.Namespace, _repo: Repository) -> int:
    file_types = [t.strip() for t in args.types.split(",")]
    policy = DownloadPolicy(file_types=file_types)
    dl = Downloader(dest_dir=args.dest, policy=policy)

    try:
        result = dl.download_one_sync(args.package, args.pkg_version)
    except Exception as exc:
        logger.debug("Unexpected error", exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if result.errors:
        for err in result.errors:
            print(f"  ERROR: {err}", file=sys.stderr)
    for f in result.files:
        print(f"  Downloaded: {f}")
    for s in result.skipped:
        print(f"  Skipped: {s}")

    print(f"\n{result.name} {result.version}: "
          f"{len(result.files)} downloaded, {len(result.skipped)} skipped, "
          f"{len(result.errors)} errors")
    return 1 if result.errors and not result.files else 0


def _cmd_download_many(args: argparse.Namespace, _repo: Repository) -> int:
    try:
        with open(args.from_file, encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        print(f"Error: file not found: {args.from_file}", file=sys.stderr)
        return 1

    if not names:
        print("No packages in file.", file=sys.stderr)
        return 1

    file_types = [t.strip() for t in args.types.split(",")]
    policy = DownloadPolicy(
        file_types=file_types,
        max_workers=args.workers,
        rate_limit=args.rate,
    )
    dl = Downloader(dest_dir=args.dest, policy=policy)

    try:
        if args.resume:
            results = dl.go_or_resume_sync(names)
        else:
            results = dl.download_many_sync(names)
    except Exception as exc:
        logger.debug("Unexpected error", exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    total_files = 0
    total_errors = 0
    for r in results:
        total_files += len(r.files)
        total_errors += len(r.errors)
        if r.errors:
            for err in r.errors:
                print(f"  {r.name}: ERROR: {err}", file=sys.stderr)
        if r.files:
            for fp in r.files:
                print(f"  {r.name}: {fp}")

    print(f"\n{len(results)} packages, {total_files} files downloaded, "
          f"{total_errors} errors")
    return 0


def _cmd_enrich(args: argparse.Namespace, repo: Repository) -> int:
    sources = {s.strip() for s in args.sources.split(",")}
    token = args.github_token

    try:
        project = repo.get_project(args.package)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.debug("Unexpected error", exc_info=True)
        print(f"Network error: {exc}", file=sys.stderr)
        return 2

    print(f"Package: {project.info.name}  {project.info.version}")

    if "downloads" in sources:
        from pypi_librarian.pypistats import fetch_download_stats
        stats = fetch_download_stats(args.package)
        if stats is None:
            print("\nDownload stats: not available on pypistats")
        else:
            print("\nDownload stats (pypistats.org):")
            print(f"  Last day:   {stats.last_day:,}")
            print(f"  Last week:  {stats.last_week:,}")
            print(f"  Last month: {stats.last_month:,}")

    if "github" in sources:
        from pypi_librarian.github import fetch_github_info_for_project
        gh = fetch_github_info_for_project(
            project.info.project_url, project.info.home_page, token=token
        )
        if gh is None:
            print("\nGitHub: no GitHub URL found or not accessible")
        else:
            print(f"\nGitHub ({gh.owner}/{gh.repo}):")
            print(f"  Stars:       {gh.stars:,}")
            print(f"  Forks:       {gh.forks:,}")
            print(f"  Open issues: {gh.open_issues:,}")
            print(f"  Last push:   {gh.last_push or '(unknown)'}")
            if gh.archived:
                print("  ** ARCHIVED **")

    if "health" in sources:
        from pypi_librarian.pypistats import fetch_download_stats
        from pypi_librarian.github import fetch_github_info_for_project
        from pypi_librarian.health import score_project

        upload_times = [
            f.upload_time
            for release in project.releases
            for f in release.files
            if f.upload_time
        ]
        dl_stats = fetch_download_stats(args.package) if "downloads" not in sources else None
        gh_data = (
            fetch_github_info_for_project(
                project.info.project_url, project.info.home_page, token=token
            )
            if "github" not in sources
            else None
        )
        health = score_project(
            project.info,
            releases_upload_times=upload_times,
            stats=dl_stats,
            github=gh_data,
        )
        print(f"\nHealth score: {health.score:.2f} / 1.00")
        if health.notes:
            print("  Issues:")
            for note in health.notes:
                print(f"    - {note}")

    return 0


def _cmd_fetch_metadata(args: argparse.Namespace, _repo: Repository) -> int:
    names = None
    if args.from_file:
        try:
            with open(args.from_file, encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except FileNotFoundError:
            print(f"Error: file not found: {args.from_file}", file=sys.stderr)
            return 1

    fm = FetchMetadata(
        dest_dir=args.dest,
        limit=args.limit,
        max_workers=args.workers,
        rate_limit=args.rate,
    )
    try:
        count = fm.run(names)
    except Exception as exc:
        logger.debug("Unexpected error", exc_info=True)
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Fetched metadata for {count} packages into {args.dest}")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s %(name)s: %(message)s",
    )

    repo = Repository()

    handlers = {
        "info": _cmd_info,
        "versions": _cmd_versions,
        "latest": _cmd_latest,
        "download": _cmd_download,
        "download-many": _cmd_download_many,
        "fetch-metadata": _cmd_fetch_metadata,
        "enrich": _cmd_enrich,
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args, repo)


if __name__ == "__main__":
    sys.exit(main())
