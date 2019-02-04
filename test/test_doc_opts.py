# coding=utf-8
"""
Test command line interface
"""

import pypi_librarian.__main__ as main

def test_main():
    main.process_docopts({"version":True})