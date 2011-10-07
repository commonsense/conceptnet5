"""
Utility functions to determine where on the filesystem this code is being run
from.
"""

import os
import sys

def module_path():
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding()))

# Define the top-level conceptnet5/ directory, where data files can be found.
PACKAGE_DIR = os.path.dirname(module_path())

def get_project_filename(path):
    """
    Get a valid path referring to a given filename in the project directory.
    """
    if PACKAGE_DIR:
        return PACKAGE_DIR + os.path.sep + path
    else:
        return path

