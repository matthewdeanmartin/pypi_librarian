# coding=utf-8
"""
generic, one off functions
"""
import os


def locate_file(file_name: str, executing_file: str) -> str:
    """
    File must exist
    :type file_name: str|unicode
    :type executing_file: str|unicode
    :return: str
    """
    # if executing_file is None:
    #     executing_file = __file__
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(executing_file)), file_name
    )
    if not os.path.exists(file_path):
        raise TypeError(file_path + " doesn't exist")
    return file_path
