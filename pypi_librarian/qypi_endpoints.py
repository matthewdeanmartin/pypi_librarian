# coding=utf-8
"""
https://pypi.org/project/qypi/

Commands:
    REPO
    list      List all packages on PyPI

  browse    List packages with given trove classifiers.
  search    Search PyPI for packages or releases thereof.

  PROJECT
  files     List files available for download.
  info      Show package details.
  owner     List package owners & maintainers
  readme    View packages' long descriptions.
  releases  List released package versions

  USER
  owned     List packages owned/maintained by a user


Functionality of qypi spread between QyPI class and command line interface.

"""
import json
from typing import List, Any
import qypi
import sys
import subprocess


def _prologue() -> List[str]:
    return [sys.executable, "-m", "qypi"]


def browse(what: str) -> Any:
    command = _prologue()
    command.extend(["browse", what])
    results = subprocess.check_output(command)
    return results.decode()


def files(project: str) -> Any:
    command = _prologue()
    command.extend(["files", project])
    results = subprocess.check_output(command).decode("utf-8")
    return results


def info(project: str) -> Any:
    command = _prologue()
    command.extend(["info", project])
    results = subprocess.check_output(command)
    return results.decode()


def list_all() -> Any:
    command = _prologue()
    command.extend(["list"])
    results = subprocess.check_output(command)
    return results.decode()


def owned(user: str) -> Any:
    command = _prologue()
    command.extend(["owned", user])
    results = subprocess.check_output(command)
    return results.decode()


def owner(project: str) -> Any:
    command = _prologue()
    command.extend(["owner", project])
    results = subprocess.check_output(command)
    return results.decode()


def search(query: str) -> Any:
    command = _prologue()
    command.extend(["search", query])
    results = subprocess.check_output(command)
    return results.decode()


def releases(project: str) -> Any:
    command = _prologue()
    command.extend(["releases", project])
    results = subprocess.check_output(command)
    return results.decode()


def readme(project: str) -> Any:
    command = _prologue()
    command.extend(["search", project])
    results = subprocess.check_output(command)
    return results.decode()


if __name__ == "__main__":
    repo_functions = list_all
    project_functions = [browse, files, info, owner, search, releases, readme]
    user_function = [owned]
    for fun in project_functions:
        print(fun("jiggle_version"))
    for fun in user_function:
        print(fun("matthewdeanmartin"))
