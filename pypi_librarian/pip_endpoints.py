# coding=utf-8
"""
Shell to pip.

Not planning on supporting every metadata command & option that pip does.

Meta Data Relevant Commands:
  download                    Download packages.

  freeze                      Output installed packages in requirements format.
  list                        List installed packages.

  show                        Show information about installed packages.
  search                      Search PyPI for packages.


"""

import subprocess
import sys
from typing import Callable, List, Optional


def _prologue() -> List[str]:
    return [sys.executable, "-m", "pip"]


def download(project_name: str, dest: str) -> bytes:
    """
    Many switches to specify which file to download
    :param project_name:
    :param dest:
    :return:
    """
    if not dest:
        raise TypeError("destination folder required")
    command = _prologue()
    command.extend(["download", project_name, "--dest={0}".format(dest)])
    return subprocess.check_output(command)


def freeze_current() -> bytes:
    """
    -r, --requirement <file>    Use the order in the given requirements file and its comments when generating output.
    This option can be used multiple times.
    -f, --find-links <url>      URL for finding packages, which will be added to the output.
    -l, --local                 If in a virtualenv that has global access, do not output globally-installed packages.
    --user                      Only output packages installed in user-site.
    --all                       Do not skip these packages in the output: setuptools, distribute, wheel, pip
    --exclude-editable          Exclude editable package from output.
      :return:
    """
    command = _prologue()
    command.extend(["freeze"])
    return subprocess.check_output(command)


def list_current() -> bytes:
    """
        -o, --outdated              List outdated packages
    -u, --uptodate              List uptodate packages
    -e, --editable              List editable projects.
    -l, --local                 If in a virtualenv that has global access, do not list globally-installed packages.
    --user                      Only output packages installed in user-site.
    --pre                       Include pre-release and development versions. By default, pip only finds stable versions.
    --format <list_format>      Select the output format among: columns (default), freeze, or json
    --not-required              List packages that are not dependencies of installed packages.
    --exclude-editable          Exclude editable package from output.
    --include-editable          Include editable package from output.

      tabular layout, columns (default), freeze, or json
      :return:
    """
    command = _prologue()
    command.extend(["list", "--format=json"])
    return subprocess.check_output(command)


def show_installed_package(project_name: str, list_files: bool = False) -> bytes:
    """
    tabular layout, columns (default), freeze, or json
    :return:
    """
    command = _prologue()
    command.extend(["show", project_name])
    if list_files:
        command.append("--files")
    return subprocess.check_output(command)


def search(query: str, base_url: Optional[str] = None) -> bytes:
    """
    output in form of
    package (1.0)      - short description

    Does not offer any alternative output formats.
    :return:
    """
    command = _prologue()
    command.extend(["search", query])
    if base_url:
        command.append("--index={0}".format(base_url))

    return subprocess.check_output(command)


if __name__ == "__main__":

    def run() -> None:
        noarg_functions: List[Callable[[], bytes]] = [freeze_current, list_current]
        for fun in noarg_functions:
            print(fun())
        project_functions: List[Callable[[str], bytes]] = [search]
        for fun in project_functions:
            print(fun("jiggle-version"))
        print(download("jiggle-version", "tmp/"))

    run()
