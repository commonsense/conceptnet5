from __future__ import unicode_literals
import argparse
import hashlib


def strhash(text):
    """
    Get a number from 0 to 255 from the first byte of the SHA1 hash
    of a string.
    """
    hashobj = hashlib.sha1(text.encode('utf-8'))
    return hashobj.digest()[0]


class EdgeDistributor(object):
    """
    Takes in tab-separated "CSV" files, and distributes their lines between
    `n` output files.

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
            open(output_dir + '/edges_%02d.csv' % i, 'w', encoding='utf-8')
            for i in range(n)
        ]
    
    def handle_file(self, filename):
        """
        Send the lines of this input file to different output files based on
        the hash of their first item.
        """
        for line in open(filename, encoding='utf-8'):
            key = line.split('\t', 1)[0]
            bucket = strhash(key) % self.n
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
    parser.add_argument('-o', default='data/collated', help='the directory in which to write output files')
    parser.add_argument('-n', type=int, default=8, help='the number of separate files to write')
    parser.add_argument('files', nargs='+', help='msgpack input files to collate')
    args = parser.parse_args()

    sorter = EdgeDistributor(args.o, args.n)
    for file in args.files:
        sorter.handle_file(file)

    sorter.close()


if __name__ == '__main__':
    run_args()
