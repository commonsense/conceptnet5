from __future__ import unicode_literals
import sys
import argparse
import codecs

# Get the version of sys.stdin that contains bytes, not Unicode.
if sys.version_info.major >= 3:
    STDIN = sys.stdin.buffer
else:
    STDIN = sys.stdin


class EdgeDistributor(object):
    """
    Takes in lines of a tab-separated "CSV" file, and distributes them
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
        Take in parameters and open the appropriate output files.
        """
        self.n = n
        self.files = [
            codecs.open(output_dir + '/edges_%02d.csv' % i, 'w', encoding='utf-8')
            for i in range(n)
        ]

    def handle_line(self, line):
        """
        Read a line, and split based on the hash of its first item.
        """
        key = line.split('\t', 1)[0]
        bucket = hash(key) % self.n
        self.files[bucket].write(line)

    def close(self):
        """
        Close all the output files when finished.
        """
        for file in self.files:
            file.close()


def run_args():
    """
    Handle command-line arguments, and run the EdgeDistributor on lines read
    from standard input.

    Unlike other builder commands, this uses standard input instead of
    taking a filename, because we often simply want to run the output of
    another step through it as a pipe.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', default='./split', help='the directory in which to write output files')
    parser.add_argument('-n', type=int, default=20, help='the number of separate files to write')
    args = parser.parse_args()

    sorter = EdgeDistributor(args.o, args.n)
    for line in STDIN:
        sorter.handle_line(line.decode('utf-8'))

    sorter.close()


if __name__ == '__main__':
    run_args()
