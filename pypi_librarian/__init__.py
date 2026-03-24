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
from pypi_librarian.models import (
    NewPackage as NewPackage,
    NewRelease as NewRelease,
    Package as Package,
    Project as Project,
    ProjectInfo as ProjectInfo,
    Release as Release,
    ReleaseFile as ReleaseFile,
    User as User,
)

__all__ = [
    "__version__",
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
