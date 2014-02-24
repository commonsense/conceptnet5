from __future__ import unicode_literals
import sys
import argparse


# Get the version of sys.stdin that contains bytes, not Unicode.
if sys.version_info.major >= 3:
    STDIN = sys.stdin.buffer
else:
    STDIN = sys.stdin


class EdgeDistributor(object):
    """
    Takes a tab-separated "CSV" file as input, and distributes its lines
    between `n` output files.

    The file to write to is determined by a hash of the first item in
    the line, so all rows with the same first item will end up in the same
    file, useful if you are about to sort and group by that item.

    In ConceptNet terms, the input file is a listing of edges, and the
    first item in the line is their assertion URI. We can then sort the
    result, and pass it to `conceptnet5.builders.combine_assertions` to
    group edges with the same assertion URI into single assertions.
    """
    def __init__(self, output_dir, n):
        """
        Take in parameters and open the appropriate output files. Use
        binary mode so that we can pass bytes through directly.
        """
        self.n = n
        self.files = [
            open(output_dir + '/edges_%02d.csv' % i, 'wb')
            for i in range(n)
        ]

    def handle_line(self, line):
        """
        Read a line (as bytes), and split based on the hash of its first item.
        """
        key_bytes = line.split(b'\t')[0]
        bucket = hash(key_bytes) % self.n
        self.files[bucket].write(line)

    def close(self):
        """
        Close all the output files when finished.
        """
        for file in self.files:
            file.close()


def run_args():
    """
    Handle command-line arguments, and run the EdgeDistributor on standard input.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', default='./split', help='the directory in which to write output files')
    parser.add_argument('-n', type=int, default=20, help='the number of separate files to write')
    args = parser.parse_args()

    sorter = EdgeDistributor(args.o, args.n)
    for line in STDIN:
        sorter.handle_line(line)

    sorter.close()


if __name__ == '__main__':
    run_args()

