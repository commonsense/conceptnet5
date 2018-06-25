import pandas as pd
import numpy as np
from sklearn.preprocessing import normalize
from .sparse_matrix_builder import build_from_conceptnet_table
from .formats import load_hdf, save_hdf


def sharded_retrofit(dense_hdf_filename, conceptnet_filename, output_filename,
                     iterations=5, nshards=6, verbosity=0,
                     max_cleanup_iters=20):
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

        retrofitted = retrofit(combined_index, dense_frame, sparse_csr, iterations, verbosity, max_cleanup_iters)
        save_hdf(retrofitted, temp_filename)
        del retrofitted


def join_shards(output_filename, nshards=6, sort=False):
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
    if sort:
        dframe.sort_index(inplace=True)
    save_hdf(dframe, output_filename)


def retrofit(row_labels, dense_frame, sparse_csr,
             iterations=5, verbosity=0, max_cleanup_iters=20):
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

    `sharded_retrofit` is responsible for building `row_labels` and `sparse_csr`
    appropriately.
    """
    # Initialize a DataFrame with rows that we know
    retroframe = pd.DataFrame(
        index=row_labels, columns=dense_frame.columns, dtype='f'
    )
    retroframe.update(dense_frame)

    # orig_weights = 1 for known vectors, 0 for unknown vectors
    orig_weights = 1 - retroframe.iloc[:, 0].isnull()
    weight_array = orig_weights.values[:, np.newaxis].astype('f')
    orig_vecs = retroframe.fillna(0).values

    # Subtract the mean so that vectors don't just clump around common
    # hypernyms
    nonzero_indices = np.abs(orig_vecs).sum(1).nonzero()
    orig_vecs[nonzero_indices] -= orig_vecs.mean(0)

    # Delete the frame we built, we won't need its indices again until the end
    del retroframe

    vecs = orig_vecs
    for iteration in range(iterations):
        if verbosity >= 1:
            print('Retrofitting: Iteration %s of %s' % (iteration+1, iterations))

        vecs = sparse_csr.dot(vecs)
        nonzero_indices = np.abs(vecs).sum(1).nonzero()
        vecs[nonzero_indices] -= vecs.mean(0)

        # use sklearn's normalize, because it normalizes in place and
        # leaves zero-rows at 0
        normalize(vecs, norm='l2', copy=False)

        # Average known rows with original vectors
        vecs += orig_vecs
        vecs /= (weight_array + 1.)

    # Clean up as many all-zero vectors as possible.  Zero vectors
    # can either come from components of the conceptnet graph that
    # don't contain any terms from the embedding we are currently
    # retrofitting (and there is nothing we can do about those here,
    # but when retrofitting is done on that embedding they should be
    # taken care of then) or from terms whose distance in the graph is
    # larger than the number of retrofitting iterations used above; we
    # propagate non-zero values to those terms by averaging over their
    # non-zero neighbors.  Note that this propagation can never reach
    # the first class of terms, so we can't necessarily expect the
    # number of zero vectors to go to zero at any one invocation of
    # this code.
    n_zero_indicators_old = -1
    for iteration in range(max_cleanup_iters):
        zero_indicators = (np.abs(vecs).sum(1) == 0)
        n_zero_indicators = np.sum(zero_indicators)
        if n_zero_indicators == 0 or n_zero_indicators == n_zero_indicators_old:
            break
        n_zero_indicators_old = n_zero_indicators
        vecs[zero_indicators, :] = sparse_csr[zero_indicators, :].dot(vecs)
        normalize(vecs[zero_indicators, :], norm='l2', copy=False)
    else:
        print('Warning: cleanup iteration limit exceeded.')

    retroframe = pd.DataFrame(data=vecs, index=row_labels, columns=dense_frame.columns)
    return retroframe
