# coding=utf-8
"""
This script processes the output of

curl -o packages.html -0 https://pypi.python.org/simple/  --location

"""
# https://python-forum.io/Thread-pip-list-available-packages

# download file
# curl!

# parse out version strings

import os
import subprocess

# https://pypi.org/simple/epicurus/
from typing import List

import requests


def execute_get_text(command: str) -> str:
    """
    Helper for shell commands
    :param command:
    :return:
    """
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as err:
        raise

    return result


def download_package(rows: str) -> None:
    """
    Download a package locally for opening & inspection
    :param rows:
    :return:
    """
    url = package_info(rows)
    if url == "nozips":
        print("no zips")
        return
    base = os.path.basename(url).split("#")[0]
    if os.path.isfile("packages/{0}".format(base)):
        print("Already have packages/{0}".format(base))
        return
    command = "curl -0 {0} -o packages/{1}".format(url, base)
    print(command)
    result = execute_get_text(command)
    print(result)


def package_info(rows: str) -> str:
    """
    Parse html sections
    :param rows:
    :return:
    """
    last = "nozips"
    for row in rows:
        try:
            url = row.split('"')[1]
            if ".zip" in url or ".gz" in url:
                print(url)
                last = url
        except:
            pass
    return last


def done_packages() -> List[str]:
    """
    See which packages have already been downloaded
    :return:
    """
    packages = []
    for directory in os.listdir("packages"):
        if directory.endswith(".gz") or directory.endswith(".zip"):
            continue
        packages.append(directory)
    print("Have " + str(len(packages)) + " packages")
    return packages


def read_packages() -> None:
    """
    Read locally cached html page with list of all packages.
    :return:
    """
    i = 0
    done = done_packages()
    for row in open("packages.html"):
        try:
            url = "https://pypi.org" + row.split('"')[1]
            package_name = row.split('"')[1].replace("simple/", "").replace("/", "")
            if package_name in done:
                print(package_name + " done")
                continue
            print(url)
        except:
            continue

        response = requests.get(url)

        with open("meta/" + url.split("/")[-2], "w") as file:
            download_package(response.text.split("\n"))
            # file.write(response.text)

        i += 1
        if i > 10000:
            exit(1)


if __name__ == "__main__":
    read_packages()
