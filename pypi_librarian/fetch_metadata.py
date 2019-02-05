# coding=utf-8
"""
Fetch meta data to folder and/or sqlite db
"""
import ntpath
import os
from typing import Callable, List
import random
import time

from pypi_librarian.qypi_endpoints import info
from pypi_librarian.json_endpoints import JsonEndpoints
from pypi_librarian.utils import locate_file


class FetchMetadata(object):
    def __init__(
        self, temp_folder: str, metadata_method: Callable, stop_at: int
    ) -> None:
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)
        self.temp_folder = temp_folder
        self.metadata_method = metadata_method
        self.stop_at = stop_at

    def generate_done_packages(self) -> List[str]:
        """
        See which packages have already been downloaded
        :return:
        """
        packages = []
        for file in os.listdir(self.temp_folder):
            # ref: https://stackoverflow.com/questions/8384737/extract-file-name-from-path-no-matter-what-the-os-path-format
            packages.append(ntpath.basename(file).replace(".json", ""))

        print("Have " + str(len(packages)) + " packages")
        return packages

    def generate_packages(self) -> None:
        """
        Read locally cached html page with list of all packages.
        :return:
        """
        i = 0
        done = self.generate_done_packages()
        packages_todo = []
        packages_html = locate_file("packages.html", __file__)
        for row in open(packages_html):
            if "simple" not in row:
                continue
            try:
                url = "https://pypi.org" + row.split('"')[1]
                package_name = row.split('"')[1].replace("simple/", "").replace("/", "")

                if package_name in done:
                    continue
            except Exception as ex:
                print(ex, row)
                continue
            try:
                packages_todo.append(package_name)
            except IndexError as ie:
                print(str(ie), package_name)

        random.shuffle(packages_todo)
        for package_name in packages_todo:
            try:
                response = self.metadata_method(package_name)
            except Exception as ex:
                print(str(ex))
                continue
            if response is None:
                print("This doesn't exist: " + str(package_name))
                continue

            file_name = package_name + ".json"
            with open(os.path.join(self.temp_folder, file_name), "w") as file:
                file.write(response)

            i += 1
            if i > self.stop_at:
                break


if __name__ == "__main__":
    # pip can't do this, it is only metadata for INSTALLED packages.
    # qypi can- but is shell for each command.
    # json enpoints can, no shell
    def run() -> None:
        t0 = time.time()

        def go():
            je = JsonEndpoints()
            invoker = je.package_json_as_text
            invoker = info
            fetcher = FetchMetadata("tmp", invoker , 20)
            fetcher.generate_packages()

        go()
        t1 = time.time()

        total = t1 - t0
        print(total)

    run()
