# coding=utf-8
"""
Pypi Librarian

Usage:

  pypi_librarian -h | --help
  pypi_librarian --version

Options:
  --version            Show version and exit.
  -h --help            Show this screen.

"""
from typing import Optional, Dict, Union
from docopt import docopt
from pypi_librarian.__init__ import __version__


def process_docopts(test: Optional[Dict[str, Union[str, bool]]] = None) -> None:
    """
    Just process the command line options and commands
    :return:
    """
    if test:
        arguments = test
    else:
        arguments = docopt(__doc__, version="Pypi Librarian {0}".format(__version__))
    print(arguments)
    print("Not supported yet.")


if __name__ == "__main__":
    process_docopts()
