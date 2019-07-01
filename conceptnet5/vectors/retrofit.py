import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from .formats import load_hdf, save_hdf
from .sparse_matrix_builder import build_from_conceptnet_table


def sharded_retrofit(
    dense_hdf_filename,
    conceptnet_filename,
    output_filename,
    iterations=5,
    nshards=6,
    verbosity=0,
    max_cleanup_iters=20,
    orig_vec_weight=0.15,
):
    # frame_box is basically a reference to a single large DataFrame. The
    # DataFrame will at times be present or absent. When it's present, the list
    # contains one item, which is the DataFrame. When it's absent, the list
    # is empty.
    frame_box = [load_hdf(dense_hdf_filename)]
    sparse_csr, combined_index = build_from_conceptnet_table(
        conceptnet_filename, orig_index=frame_box[0].index
    )
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

        retrofitted = retrofit(
            combined_index,
            dense_frame,
            sparse_csr,
            iterations,
            verbosity,
            max_cleanup_iters,
            orig_vec_weight,
        )
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
        joined_matrix[:, (ncols * i) : (ncols * (i + 1))] = shard.values
        del shard

    normalize(joined_matrix, axis=1, norm='l2', copy=False)
    dframe = pd.DataFrame(joined_matrix, index=joined_labels)
    if sort:
        dframe.sort_index(inplace=True)
    save_hdf(dframe, output_filename)


def retrofit(
    row_labels,
    dense_frame,
    sparse_csr,
    iterations=5,
    verbosity=0,
    max_cleanup_iters=20,
    orig_vec_weight=0.15,
):
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
    retroframe = pd.DataFrame(index=row_labels, columns=dense_frame.columns, dtype='f')
    retroframe.update(dense_frame)

    # orig_weights = 1 for known vectors, 0 for unknown vectors
    orig_weights = 1 - retroframe.iloc[:, 0].isnull()
    orig_vec_indicators = orig_weights.values != 0
    orig_vecs = retroframe.fillna(0).values

    # Subtract the mean so that vectors don't just clump around common
    # hypernyms
    orig_vecs[orig_vec_indicators] -= orig_vecs[orig_vec_indicators].mean(0)

    # Delete the frame we built, we won't need its indices again until the end
    del retroframe

    vecs = orig_vecs
    for iteration in range(iterations):
        if verbosity >= 1:
            print('Retrofitting: Iteration %s of %s' % (iteration + 1, iterations))

        # Since the sparse weight matrix is row-stochastic and has self-loops,
        # pre-multiplication by it replaces each vector by a weighted average
        # of itself and its neighbors.  We really want to take the average
        # of (itself and) the nonzero neighbors, which we can do by dividing
        # the average with all the neighbors by the total of the weights of the
        # nonzero neighbors.  This avoids unduly shrinking vectors assigned to
        # terms with lots of zero neighbors.

        # Find, for every term, the total weight of its nonzero neighbors.
        nonzero_indicators = np.abs(vecs).sum(1) != 0
        total_neighbor_weights = sparse_csr.dot(nonzero_indicators)

        # Now average with all the neighbors.
        vecs = sparse_csr.dot(vecs)

        # Now divide each vector (row) by the associated total weight.
        # Some of the total weights could be zero, but only for rows that,
        # before averaging, were zero and had all neighbors zero, whence
        # after averaging will be zero.  So only do the division for rows
        # that are nonzero now, after averaging.  Also, we reshape the total
        # weights into a column vector so that numpy will broadcast the
        # division by weights across the columns of the embedding matrix.
        nonzero_indicators = np.abs(vecs).sum(1) != 0
        total_neighbor_weights = total_neighbor_weights[nonzero_indicators]
        total_neighbor_weights = total_neighbor_weights.reshape(
            (len(total_neighbor_weights), 1)
        )
        vecs[nonzero_indicators] /= total_neighbor_weights

        # Re-center the (new) non-zero vectors.
        vecs[nonzero_indicators] -= vecs[nonzero_indicators].mean(0)

        # Average known rows with original vectors
        vecs[orig_vec_indicators, :] = (1.0 - orig_vec_weight) * vecs[
            orig_vec_indicators, :
        ] + orig_vec_weight * orig_vecs[orig_vec_indicators, :]

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
        zero_indicators = np.abs(vecs).sum(1) == 0
        n_zero_indicators = np.sum(zero_indicators)
        if n_zero_indicators == 0 or n_zero_indicators == n_zero_indicators_old:
            break
        n_zero_indicators_old = n_zero_indicators
        # First replace each zero vector (row) by the weighted average of all its
        # neighbors.
        vecs[zero_indicators, :] = sparse_csr[zero_indicators, :].dot(vecs)
        # Now divide each newly nonzero vector (row) by the total weight of its
        # old nonzero neighbors.
        new_nonzero_indicators = np.logical_and(
            zero_indicators, np.abs(vecs).sum(1) != 0
        )
        total_neighbor_weights = sparse_csr[new_nonzero_indicators, :].dot(
            np.logical_not(zero_indicators)
        )
        total_neighbor_weights = total_neighbor_weights.reshape(
            (len(total_neighbor_weights), 1)
        )
        vecs[new_nonzero_indicators, :] /= total_neighbor_weights
    else:
        print('Warning: cleanup iteration limit exceeded.')

    retroframe = pd.DataFrame(data=vecs, index=row_labels, columns=dense_frame.columns)
    return retroframe
