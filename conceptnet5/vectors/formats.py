import pandas as pd
import numpy as np
from scipy import sparse


def load_glove(filename, nrows=500000):
    return pd.read_table(
        filename, sep=' ', index_col=0, quoting=3,
        keep_default_na=False, na_values=[],
        names=['term'] + list(range(300)),
        nrows=nrows
    )


def load_hdf(filename):
    return pd.read_hdf(filename, 'mat')


def save_hdf(table, filename):
    return table.to_hdf(filename, 'mat')


def save_csr(matrix, filename):
    np.savez(filename, data=matrix.data, indices=matrix.indices,
                indptr=matrix.indptr, shape=matrix.shape)


def load_csr(filename):
    with np.load(filename) as npz:
        mat = sparse.csr_matrix((npz['data'], npz['indices'], npz['indptr']), shape=npz['shape'])
    return mat

