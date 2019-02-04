# coding=utf-8
"""
Test if version is most recent
"""
from pypi_librarian import Repository
from pypi_librarian._version import __version__

def test_get_vers():
    # scenarios
    # - not in repo yet.
    # - compare to currently executing (e.g. start up task to warn user that this lib is out of date or to trigger
    # upgrade)
    # - compare currently installed to pypi (lots of apps specifically for this)
    repo = Repository()
    project = repo.get_project("jiggle_version")
    current = project.current_package()
    if current.version == __version__:
        print("Currently executing is latest")
    else:
        # python world doesn't follow any single versioning system, so saying if 1 version is lesser or greater is
        # non-trivial.
        print("Not same as latest : {0} vs {1}".format(__version__, current.version) )


# # OK.... this is failing on basic scenarios.
# def test_pkginfo():
#     import pkginfo
#     # fails.
#     ins = pkginfo.utils.Installed("jiggle_version")
#     x = ins.read()
#     print(x)


# def test_pkg_info():
# import pkg_info
#     # this makes a call to pypi
#     info = pkg_info.get_pkg_info("jiggle_version")
#     # pretty good deserialization of the json object for a package/project
#     # and that is it. Lib has no other fetaures.
#     print(info)

