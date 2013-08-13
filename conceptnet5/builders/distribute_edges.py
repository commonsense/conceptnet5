import sys
import argparse


class EdgeDistributor(object):
    def __init__(self, output_dir, n):
        self.n = n
        self.files = [
            open(output_dir + '/edges_%03d.csv' % i, 'w')
            for i in range(n)
        ]

    def handle_line(self, line):
        uri = line.split('\t')[0]
        bucket = hash(uri) % self.n
        self.files[bucket].write(line)

    def close(self):
        for file in self.files:
            file.close()


def run_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', default='./split', help='the directory in which to write output files')
    parser.add_argument('-n', type=int, default=256, help='the number of separate files to write')
    args = parser.parse_args()

    sorter = EdgeDistributor(args.o, args.n)
    for line in sys.stdin:
        sorter.handle_line(line)

    sorter.close()


if __name__ == '__main__':
    run_args()

