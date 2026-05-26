# coding=utf-8
"""
pypi_librarian — a library for querying and downloading PyPI package metadata.

Quick start::

    from pypi_librarian import Repository

    repo = Repository()
    project = repo.get_project("requests")
    print(project.info.version)
"""

from pypi_librarian._version import __version__ as __version__
from pypi_librarian.class_repo import Repository as Repository
from pypi_librarian.download import Downloader as Downloader
from pypi_librarian.download import DownloadPolicy as DownloadPolicy
from pypi_librarian.download import DownloadResult as DownloadResult
from pypi_librarian.github import GitHubInfo as GitHubInfo
from pypi_librarian.health import HealthScore as HealthScore
from pypi_librarian.models import NewPackage as NewPackage
from pypi_librarian.models import NewRelease as NewRelease
from pypi_librarian.models import Package as Package
from pypi_librarian.models import Project as Project
from pypi_librarian.models import ProjectInfo as ProjectInfo
from pypi_librarian.models import Release as Release
from pypi_librarian.models import ReleaseFile as ReleaseFile
from pypi_librarian.models import User as User
from pypi_librarian.pypistats import DownloadStats as DownloadStats

__all__ = [
    "__version__",
    "DownloadPolicy",
    "DownloadResult",
    "DownloadStats",
    "Downloader",
    "GitHubInfo",
    "HealthScore",
    "NewPackage",
    "NewRelease",
    "Package",
    "Project",
    "ProjectInfo",
    "Release",
    "ReleaseFile",
    "Repository",
    "User",
]
