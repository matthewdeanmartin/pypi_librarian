# coding=utf-8
"""

Yolk does nothing that other endpoints don't already do, but is able to query local packages in a way you can't query pypi.

I think.

Yolk has a lot of overlap with pip.
-------
yolk --list == pip list -- table of installed + location
pip freeze -- installed + version
yolk --metadata  == pip show yolk -- PKG_INFO dump of named package
yolk --depends == pip graph (sort of)



Query installed Python packages:
  -l, --list            list all Python packages installed by distutils or
                        setuptools. Use PKG_SPEC to narrow results
  -a, --activated       list activated packages installed by distutils or
                        setuptools. Use PKG_SPEC to narrow results
  -n, --non-activated   list non-activated packages installed by distutils or
                        setuptools. Use PKG_SPEC to narrow results
  -m, --metadata        show all metadata for packages installed by setuptools
                        (use with -l -a or -n)
  -f FIELDS, --fields FIELDS
                        show specific metadata (comma-separated) fields; use
                        with -m or -M
  -d PKG_SPEC, --depends PKG_SPEC
                        show dependencies for a package installed by
                        setuptools if they are available
  --entry-points MODULE
                        list entry points for a module. e.g. --entry-points
                        nose.plugins
  --entry-map PACKAGE_NAME
                        list entry map for a package. e.g. --entry-map yolk

"""
