import pandas as pd
import numpy as np
from scipy.sparse import coo_matrix
from sklearn.preprocessing import normalize
from conceptnet5.vectors.evaluation.wordsim import evaluate


def retrofit(row_labels, dense_frame, sparse_csr, iterations=5, verbosity=1):
    """
    Retrofitting is a process of combining information from a machine-learned
    space of term vectors with further structured information about those
    terms. It was originally presented in this 2015 NAACL paper by Manaal
    Faruqui, Jesse Dodge, Sujay Jauhar, Chris Dyer, Eduard Hovy, and Noah
    Smith, "Retrofitting Word Vectors to Semantic Lexicons":

        https://www.cs.cmu.edu/~hovy/papers/15HLT-retrofitting-word-vectors.pdf

    This function implements a variant that I've been calling "wide
    retrofitting", which extends the process to learn vectors for terms that
    were outside the original space.

    `row_labels` is the list of terms that we want to have vectors for.

    `dense_frame` is a DataFrame assigning vectors to some of these terms.

    `sparse_csr` is a SciPy sparse square matrix, whose rows and columns are
    implicitly labeled with `row_labels`. The entries of this matrix are
    positive for terms that we know are related from our structured data.
    (This is an awkward form of input, but unfortunately there is no good
    way to represent sparse labeled data in Pandas.)

    See cli.py for an example of how to build `row_labels` and `sparse_csr`
    appropriately.
    """
    # Initialize a DataFrame with rows that we know
    retroframe = pd.DataFrame(
        index=row_labels, columns=dense_frame.columns, dtype='f'
    )
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
