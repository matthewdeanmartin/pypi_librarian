# coding=utf-8
"""
pypi-librarian — CLI for querying PyPI metadata.

Usage examples::

    pypi-librarian info requests
    pypi-librarian versions requests
    pypi-librarian latest
    pypi-librarian info requests --log-level DEBUG
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from pypi_librarian._version import __version__
from pypi_librarian.class_repo import Repository

__all__ = ["main"]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pypi-librarian",
        description="Query PyPI package metadata from the command line.",
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
    }
    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        return 1
    return handler(args, repo)


if __name__ == "__main__":
    sys.exit(main())
