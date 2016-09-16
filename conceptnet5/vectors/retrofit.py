import pandas as pd
import numpy as np
from sklearn.preprocessing import normalize
from .sparse_matrix_builder import build_from_conceptnet_table
from .formats import load_hdf, save_hdf
from sklearn.preprocessing import normalize


def sharded_retrofit(dense_hdf_filename, conceptnet_filename, output_filename,
                     iterations=5, nshards=6, verbose=1):
    # frame_box is basically a reference to a single large DataFrame. The
    # DataFrame will at times be present or absent. When it's present, the list
    # contains one item, which is the DataFrame. When it's absent, the list
    # is empty.
    frame_box = [load_hdf(dense_hdf_filename)]
    sparse_csr, combined_index = build_from_conceptnet_table(conceptnet_filename, orig_index=frame_box[0].index)
    shard_width = frame_box[0].shape[1] // nshards

    for i in range(nshards):
        temp_filename = output_filename + '.shard%d' % i
        shard_from = shard_width * i
        shard_to = shard_from + shard_width
        if len(frame_box) == 0:
            frame_box.append(load_hdf(dense_hdf_filename))
        dense_frame = pd.DataFrame(frame_box[0].iloc[:, shard_from:shard_to])

        # Delete full_dense_frame while running retrofitting, because it takes
        # up a lot of memory and we can reload it from disk later.
        frame_box.clear()

        retrofitted = retrofit(combined_index, dense_frame, sparse_csr, iterations, verbose)
        save_hdf(retrofitted, temp_filename)
        del retrofitted


def join_shards(output_filename, nshards=6):
    joined_matrix = None
    joined_labels = None
    for i in range(nshards):
        shard = load_hdf(output_filename + '.shard%d' % i)
        nrows, ncols = shard.shape
        if joined_matrix is None:
            joined_matrix = np.zeros((nrows, ncols * nshards), dtype='f')
            joined_labels = shard.index
        joined_matrix[:, (ncols * i):(ncols * (i + 1))] = shard.values
        del shard

    normalize(joined_matrix, axis=1, norm='l2', copy=False)
    dframe = pd.DataFrame(joined_matrix, index=joined_labels)
    save_hdf(dframe, output_filename)


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
    orig_weights = 1 - retroframe.iloc[:, 0].isnull()
    weight_array = orig_weights.values[:, np.newaxis].astype('f')
    orig_vecs = retroframe.fillna(0).values

    # Subtract the mean so that vectors don't just clump around common
    # hypernyms
    orig_vecs -= orig_vecs.mean(0)

    # Delete the frame we built, we won't need its indices again until the end
    del retroframe

    vecs = orig_vecs
    for iteration in range(iterations):
        if verbosity >= 1:
            print('Retrofitting: Iteration %s of %s' % (iteration+1, iterations))

        vecs = sparse_csr.dot(vecs)
        vecs -= vecs.mean(0)

        # use sklearn's normalize, because it normalizes in place and
        # leaves zero-rows at 0
        normalize(vecs, norm='l2', copy=False)

        # Average known rows with original vectors
        vecs += orig_vecs
        vecs /= (weight_array + 1.)

    retroframe = pd.DataFrame(data=vecs, index=row_labels, columns=dense_frame.columns)
    return retroframe
