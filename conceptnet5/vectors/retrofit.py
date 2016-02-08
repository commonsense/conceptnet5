import pandas as pd
import numpy as np
from scipy.sparse import coo_matrix
from sklearn.preprocessing import normalize
from conceptnet5.vectors.evaluation.wordsim import evaluate


def retrofit(row_labels, dense_frame, sparse_csr, iterations=5, verbosity=1):
    retroframe = pd.DataFrame(index=row_labels, columns=dense_frame.columns)
    retroframe.update(dense_frame)
    # weight = 2 for known vectors, 1 for unknown vectors
    orig_weights = 1 - retroframe[0].isnull()
    weight_array = orig_weights.values[:, np.newaxis]
    orig_vecs = retroframe.fillna(0).values

    # Delete the frame we built, we won't need its indices again until the end
    del retroframe

    vecs = orig_vecs
    for iteration in range(iterations):
        if verbosity >= 1:
            print('Retrofitting: Iteration %s of %s' % (iteration+1, iterations))

        vecs = sparse_csr.dot(vecs)

        # use sklearn's normalize, because it normalizes in place and
        # leaves zero-rows at 0
        normalize(vecs, norm='l2', copy=False)

        # Average known rows with original vectors
        vecs += orig_vecs
        vecs /= (weight_array + 1.)
        retroframe = pd.DataFrame(data=vecs, index=row_labels, columns=dense_frame.columns)
        if verbosity >= 1:
            print(evaluate(retroframe))
            print()

    return retroframe
