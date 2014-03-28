import pkg_resources
import os

def get_data_filename(filename):
    """
    Get a valid path referring to a given filename in the `support_data`
    directory.
    """
    return pkg_resources.resource_filename('conceptnet5', os.path.join('support_data', filename))
