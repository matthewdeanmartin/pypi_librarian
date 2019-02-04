pypi_librarian
--------------

A more generic library for dowlonading packages from pypi. 

How this relates to other tools that download things from pypi:
- bandersnatch - too focused on being a mirror for pypi
- pip - too focused on package installation
- twine - too focused on package upload
- pipenv - too focused on package installation
- requests - unaware of any specific feature of pypi/warehouse
- pypi_xmlrpc - only uses the xmlrpc endpoints, which are to be deprecated some day.

Specific Scenarios
----
Let's say you want to download all the gzip/zip files for the latest version of your app and put them in a folder so you can do static code analysis on your dependencies. 

Let's say you are writing a linting tool and would like to test it on a large number of real world code bases.

Monitoring PyPi for certain events (new packages, etc.)

Schema
----
**Repository have projects.** These projects can be searched, downloaded in bulk and have various change notification strategies for mirrors

**Projects have maintainers and releases.** One of these releases is the main, most recent release that people care about. The rest are history. Pypi itself doesn't provide change notification, nor download stats. This is now provided by third party services.

**Releases have a package.** The package is a compressed file, either gz, zip or wheel which has some meta data in it as a file, PKG_INFO and more. Dependencies could be in setup.py, requirements.txt or Pipfile or nowhere.


Existing Solutions
---
[Yolk](https://pypi.org/project/yolk3k/) Command line, queries package metadata

[Pip](https://pypi.org/project/pip/) - Has some search & meta data functionality. Explicitly says that it should not be used as library but only as shell command.

[qypi](https://pypi.org/project/qypi/) - strictly fetches meta data. Outputs json.

Parsing the setup.py/PKG_INFO files
-----
- [pkginfo](https://pypi.org/project/pkginfo/) - attempts to read PKG_INFO if it can find it. I couldn't get it to work.
- [pkg_info](https://pypi.org/project/pkg_info/) - appears to be a tiny script that queries pypi for the same

similar things
- [bento](https://pypi.org/project/bento/) - a tool for making pip compatible packages, using a yaml-like bento file instead of a setup.py file
- [poetry](https://poetry.eustace.io/docs/pyproject/) - creates packages, uses a pypackage.toml file 
- [pipenv](https://poetry.eustace.io/docs/pipenv/) The pipfile Toml file is a sort of metadata file.


Package Statitics
----
[Libraries.io](https://libraries.io/api) Numerous REST enpoints, no python client that I can find yet.

[pypistats](https://github.com/hugovk/pypistats) output version info in many formats. Serves data from https://pypistats.org/api/ - which is from the official PyPi "big table" records.

[pkginfo](https://pypi.org/project/pkginfo/) Parses pkg info file found in package gz/zip/whl files


Pypi mirrors
------------
Bandersnatch

[Dumb-pypi](https://github.com/chriskuehl/dumb-pypi)


Commercial Package Repos
---
I plan to implement support for pypi & compatible mirrors first.

- packagecloud.io
- gemfury
