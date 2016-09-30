import pkg_resources
import os

DATA_DIR = os.environ.get('CONCEPTNET_DATA') or os.environ.get('CONCEPTNET_BUILD_DATA') or os.path.expanduser('~/.conceptnet5')
if not os.path.exists(DATA_DIR):
    DATA_DIR = 'data'


def get_support_data_filename(filename):
    """
    Get a valid path referring to a given filename in the `support_data`
    directory. This is for data files that are included in the conceptnet
    package, such as for testing.
    """
    return pkg_resources.resource_filename(
        'conceptnet5', os.path.join('support_data', filename)
    )


def get_data_filename(filename):
    """
    Get a path referring to a given filename in ConceptNet 5's external
    data directory. This directory can be specified with the environment
    variable CONCEPTNET_DATA, and defaults to `~/.conceptnet5` -- which,
    if you've run `data/Makefile`, is a symlink pointing to the data
    directory.

    Unlike the `support_data` directory, this directory is not distributed
    with ConceptNet, generally because the files it contains are too large.
    """
    return os.path.join(DATA_DIR, filename)
