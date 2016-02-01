import pandas as pd
import numpy as np
from scipy.sparse import coo_matrix
from sklearn.preprocessing import normalize
from .formats import load_hdf, save_hdf


def retrofit(row_labels, dense_frame, sparse_csr, iterations=10, verbose=True):
    retroframe = pd.DataFrame(index=row_labels, columns=dense_frame.columns)
    retroframe.update(dense_frame)
    # weight = 2 for known vectors, 1 for unknown vectors
    weights = retroframe[0].isnull() + 1
    weight_array = weights.values[:, np.newaxis]
    orig_vecs = retroframe.fillna(0).values

    # Delete the frame we built, we won't need its indices again until the end
    del retroframe

    vecs = orig_vecs
    for iteration in range(iterations):
        if verbose:
            print('Iteration %s of %s' % (iteration+1, iterations))
            vecs = sparse_csr.dot(vecs)

            # use sklearn's normalize, because it normalizes in place and
            # leaves zero-rows at 0
            normalize(vecs, norm='l2', copy=False)

            # Average known rows with original vectors
            vecs += orig_vecs
            vecs /= weight_array

    retroframe = pd.DataFrame(data=vecs, index=row_labels, columns=dense_frame.columns)
    return retroframe


def run_retrofit(dense_hdf_filename, conceptnet_filename, output_filename, iterations=10, verbose=True):
    dense_frame = load_hdf(dense_hdf_filename)
    sparse_csr, combined_index = build_from_conceptnet_table(DATA_PATH / 'assoc/reduced.csv', orig_index=dense_frame.index)
    retrofitted = retrofit(combined_index, dense_frame, sparse_csr, iterations, verbose)
    save_hdf(retrofitted, output_filename)
