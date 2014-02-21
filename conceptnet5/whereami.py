"""
Utility functions to determine where on the filesystem this code is being run
from.
"""

import os

def module_path():
    return os.path.dirname(__file__) or os.getcwd()

# Define the top-level conceptnet5/ directory, where data files can be found.
PACKAGE_DIR = os.path.dirname(module_path())

def get_project_filename(path):
    """
    Get a valid path referring to a given filename in the project directory.
    """
    if PACKAGE_DIR:
        return os.path.join(PACKAGE_DIR, path)
    else:
        return path

if __name__ == '__main__':
    print(get_project_filename('data'))
