import pandas as pd
import numpy as np
from scipy import sparse
import gzip
import struct
from .transforms import l1_normalize_columns, l2_normalize_rows, standardize_row_labels


def load_hdf(filename):
    return pd.read_hdf(filename, 'mat', encoding='utf-8')


def save_hdf(table, filename):
    return table.to_hdf(filename, 'mat', encoding='utf-8')


def convert_glove(glove_filename, output_filename, nrows):
    """
    Convert GloVe data from a gzipped text file to a Feather dataframe.
    """
    glove_raw = load_glove(glove_filename, nrows)
    glove_std = standardize_row_labels(glove_raw)
    del glove_raw
    glove_normal = l2_normalize_rows(l1_normalize_columns(glove_std))
    del glove_std
    save_hdf(glove_normal, output_filename)


def convert_word2vec(word2vec_filename, output_filename, nrows):
    """
    Convert word2vec data from its gzipped binary format to a Feather
    dataframe.
    """
    w2v_raw = load_word2vec_bin(word2vec_filename, nrows)
    w2v_std = standardize_row_labels(w2v_raw)
    del w2v_raw
    w2v_normal = l2_normalize_rows(l1_normalize_columns(w2v_std))
    del w2v_std
    save_hdf(w2v_normal, output_filename)


def load_glove(filename, nrows=500000):
    with gzip.open(filename, 'rt') as infile:
        return pd.read_table(
            infile, sep=' ', index_col=0, quoting=3,
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


def save_csr(matrix, filename):
    np.savez(filename, data=matrix.data, indices=matrix.indices,
             indptr=matrix.indptr, shape=matrix.shape)


def load_labels_and_npy(label_file, npy_file):
    labels = [line.rstrip('\n') for line in open(label_file, encoding='utf-8')]
    npy = np.load(npy_file)
    return pd.DataFrame(npy, index=labels, dtype='f')


def load_labels_as_index(label_file):
    labels = [line.rstrip('\n') for line in open(label_file, encoding='utf-8')]
    return pd.Index(labels)


def load_csr(filename):
    with np.load(filename) as npz:
        mat = sparse.csr_matrix((npz['data'], npz['indices'], npz['indptr']), shape=npz['shape'])
    return mat
