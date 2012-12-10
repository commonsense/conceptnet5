
import sys
from cn4_flat_file_writer import FlatFileWriter

# This file must be run while config.py points to the "nadya" database instead
# of "ConceptNet".
#
# Unfortunately, all of this was done before Django had multi-database support.


"""
This script is used to pull the conceptnet4 data into a set of flat 
files.  This way it can be read through quicker when creating 
the conceptnet5 edges with the conceptnet4 data.
"""


if __name__ == '__main__':

    if "--build_flat_files" in sys.argv:
        quickWriter = FlatFileWriter("raw_data/conceptnet4_nadya_flat_")
        quickWriter.start()
