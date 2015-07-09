import numpy as np
import sys

def main(size, out_file, stdin=sys.stdin):
    vecs = np.zeros(shape=(size, 300), dtype=float)
    for index, line in enumerate(stdin):
        vecs[index] = [float(x) for x in line.split()]
    np.save(out_file, vecs)

if __name__ == '__main__':
    main(int(sys.argv[1]), sys.argv[2])
