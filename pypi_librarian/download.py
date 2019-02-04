# coding=utf-8
"""
Code to download a package.

Not to install it, but to download it, unzip it, etc.
"""

from typing import List, Dict


class Downloader(object):
    def __init__(
        self, packages: List[str], target_folder: str, policy: Dict[str, bool]
    ) -> None:
        self.packages = packages
        self.target_folder = target_folder
        for key in policy:
            if key not in ["unzip", "keep_zips"]:
                raise TypeError("policy keys must be 'unzip' and 'keep_zips'")
        self.unzip = policy.get("unzip", False)
        self.keep_zip = policy.get("keep_zips", False)

    def redo_all(self):
        raise NotImplementedError()

    def go_or_resume(self):
        raise NotImplementedError()
