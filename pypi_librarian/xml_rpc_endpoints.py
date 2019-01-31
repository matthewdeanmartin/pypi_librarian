# coding=utf-8
"""
NB: If you get the SSL error on mac, you may need to run:

/Applications/Python 3.6/Install Certificates.command

Lots of docs:
https://warehouse.readthedocs.io/api-reference/xml-rpc/


# Journal of all things that have happened since point in time.
#
# import xmlrpc.client
# >>> import arrow
# >>> client = xmlrpc.client.ServerProxy('https://test.pypi.org/pypi')
# >>> latefeb = arrow.get('2018-02-20 10:00:00')
# >>> latefeb.timestamp
# 1519120800
# >>> latefebstamp = latefeb.timestamp
# >>> recentchanges = client.changelog(latefebstamp)
# >>> len(recentchanges)
# 7322
# >>> for entry in recentchanges:
# ...     if entry[0] == 'twine':
# ...         print(entry[1], " ", entry[3], " ", entry[2])
#
# """
import pypi_xmlrpc


def list_packages() -> None:
    """
    List all packages using xmlrpc
    :return:
    """
    try:
        import xmlrpclib
    except ImportError:
        import xmlrpc.client as xmlrpclib

    client = xmlrpclib.ServerProxy("https://pypi.python.org/pypi")
    # get a list of package names
    packages = client.list_packages()


if __name__ == "__main__":

    def run() -> None:
        """
        Exercise code
        :return:
        """
        name = "jiggle_version"
        user = "matthewdeanmartin"
        version = "1.0.68"
        # x = pypi_xmlrpc.list_packages()	# return list of all server packages
        # print(x)
        x = pypi_xmlrpc.package_releases(
            name, show_hidden=True
        )  # return list of package releases
        print(x)
        x = pypi_xmlrpc.package_roles(name)  # return list of package roles
        print(x)
        x = pypi_xmlrpc.release_data(
            name, version
        )  # return dictionary with release data
        print(x)
        x = pypi_xmlrpc.release_urls(name, version)  # return list of release urls
        print(x)
        x = pypi_xmlrpc.user_packages(user)  # return list of user packages
        print(x)
        #

    run()
