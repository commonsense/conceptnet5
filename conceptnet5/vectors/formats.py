import pandas as pd
import numpy as np
from scipy import sparse
import gzip
import struct


def load_glove(filename, nrows=500000):
    return pd.read_table(
        filename, sep=' ', index_col=0, quoting=3,
        keep_default_na=False, na_values=[],
        names=['term'] + list(range(300)),
        nrows=nrows
    )


def _read_until_space(file):
    chars = []
    while True:
        newchar = file.read(1)
        if newchar == b'' or newchar == b' ':
            break
        chars.append(newchar[0])
    return bytes(chars).decode('utf-8')


def _read_vec(file, ndims):
    fmt = 'f' * ndims
    bytes_in = file.read(4 * ndims)
    values = list(struct.unpack(fmt, bytes_in))
    return np.array(values)


def load_word2vec_bin(filename, nrows):
    label_list = []
    vec_list = []
    with gzip.open(filename, 'rb') as infile:
        header = infile.readline().rstrip()
        nrows_str, ncols_str = header.split()
        nrows = min(int(nrows_str), nrows)
        ncols = int(ncols_str)
        for row in range(nrows):
            label = _read_until_space(infile)
            vec = _read_vec(infile, ncols)
            if label == '</s>':
                # Skip the word2vec sentence boundary marker, which will not
                # correspond to anything in other data
                continue
            label_list.append(label)
            vec_list.append(vec)
    mat = np.array(vec_list)
    return pd.DataFrame(mat, index=label_list, dtype='f')


def load_hdf(filename):
    return pd.read_hdf(filename, 'mat', encoding='utf-8')


def save_hdf(table, filename):
    return table.to_hdf(filename, 'mat', encoding='utf-8')


def save_csr(matrix, filename):
    np.savez(filename, data=matrix.data, indices=matrix.indices,
                indptr=matrix.indptr, shape=matrix.shape)


def load_labels_and_npy(label_file, npy_file):
    labels = [line.rstrip('\n') for line in open(label_file, encoding='utf-8')]
    npy = np.load(npy_file)
    return pd.DataFrame(npy, index=labels, dtype='f')


def load_csr(filename):
    with np.load(filename) as npz:
        mat = sparse.csr_matrix((npz['data'], npz['indices'], npz['indptr']), shape=npz['shape'])
    return mat

