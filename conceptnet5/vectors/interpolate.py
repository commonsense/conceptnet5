# coding: utf-8
import pandas as pd
import numpy as np
from ..vectors import similar_to_vec, weighted_average
from ..transforms import l2_normalize_rows


def dataframe_svd_projection(frame, k):
    """
    Factor a dataframe into two matrices with `k` columns, using the labels
    from the dataframe as the row labels.

    The matrices that are returned are `uframe` and `vframe`. `uframe` assigns
    a k-dimensional vector to each row of the frame, and `vframe` assigns a
    k-dimensional vector to each column. One way to think of these is that
    `uframe` contains the rows of `frame` projected into a k-dimensional space,
    while `vframe` is the operation that projects those rows.

    In SVD terms, after `frame` has been factored into U @ Σ @ V^T,
    `uframe` is U @ sqrt(Σ), and `vframe` is V @ sqrt(Σ).
    """
    U, Σ, Vt = np.linalg.svd(frame.values, full_matrices=False)
    projected = U * Σ ** .5
    projection = Vt.T * Σ ** .5
    uframe = pd.DataFrame(projected[:, :k], index=frame.index, dtype='f')
    vframe = pd.DataFrame(projection[:, :k], index=frame.columns, dtype='f')
    return uframe, vframe


def merge_interpolate(frame1, frame2, extra_labels, vocab_threshold=50000, verbose=False):
    """
    Merge together two matrices of term vectors with different vocabularies.
    This is used, for instance, to merge word2vec with GloVe.

    `frame1` and `frame2` are DataFrames containing the term vectors to be
    merged, and `extra_labels` is an Index containing the terms that we want
    to infer vectors for. A term will appear in the combined matrix if it
    appears in at least two of `frame1.index`, `frame2.index`, and
    `extra_labels`.
    """
    vocab_intersection = frame1.index & frame2.index

    # Get the N most common terms from each vocabulary that are also present
    # in the other vocabulary, where N is `vocab_threshold`. There are somewhere
    # between N and 2N of these terms because the most common terms presumably
    # overlap. These terms will be used as reference points when interpolating
    # vectors for other words.
    shared_vocab = frame1.index & frame2.index
    common1 = (frame1.index & frame2.index)[:vocab_threshold]
    common2 = (frame2.index & frame1.index)[:vocab_threshold]
    common_vocab = common1 | common2

    # Find the terms that are in one of the given frames and in `extra_labels`.
    # These are the terms that we need to interpolate vectors for.
    interpolated_vocab_1 = (frame1.index.difference(frame2.index)) & extra_labels
    interpolated_vocab_2 = (frame2.index.difference(frame1.index)) & extra_labels
    new_labels = interpolated_vocab_1 | interpolated_vocab_2
    full_labels = vocab_intersection | new_labels

    # Make a matrix that concatenates the vectors that appear in both vocabularies.
    k1 = frame1.shape[1]
    k2 = frame2.shape[1]
    shared_vecs = pd.DataFrame(index=vocab_intersection, columns=range(k1 + k2), dtype='f')
    # In pandas, .loc indices are *inclusive* of their endpoints, which is why
    # we assign k1 columns from 0 to k1 - 1.
    shared_vecs.loc[vocab_intersection, 0:k1 - 1] = frame1.loc[vocab_intersection]
    shared_vecs.loc[vocab_intersection, k1:] = frame2.loc[vocab_intersection].rename(columns=lambda x: x + k1)

    # Factor the concatenated matrix using SVD.
    projected, projection = dataframe_svd_projection(shared_vecs, k1)

    # Select the vectors for sufficiently common words, which will be used as
    # the reference points.
    reference_vecs = projected.loc[common_vocab]

    # Build a matrix that will contain our final term vectors. We already know
    # the vectors for terms that appear in both vocabularies, because they're the
    # rows of `projected`, so we'll assign those to start.
    all_vecs = pd.DataFrame(index=full_labels, columns=range(k1), dtype='f')
    all_vecs.loc[vocab_intersection] = projected.loc[vocab_intersection]

    # Interpolate the remaining vectors.
    for i, label in enumerate(new_labels):
        # Make a (k1 + k2)-dimensional vector for the term, setting whichever
        # of the dimensions we know.
        vec = np.zeros(k1 + k2)
        nonzero = False
        if label in frame1.index:
            vec[:k1] = frame1.loc[label].values
            nonzero = True
        if label in frame2.index:
            vec[k1:] = frame2.loc[label].values
            nonzero = True
        assert nonzero

        # Project it into the new space, using the same matrix that projects
        # the overlapping vectors.
        query_vec = vec.dot(projection)

        # Get some similar common terms
        most_similar = similar_to_vec(reference_vecs, query_vec, num=5)
        similar_list = ', '.join(most_similar.index)
        if i % 100 == 0:
            print("%s => %s" % (label, similar_list))

        # Our new interpolated vector is the weighted average of the vectors
        # for these similar terms, weighted by how similar they are.
        interpolated_vec = weighted_average(reference_vecs, most_similar)
        all_vecs.loc[label] = interpolated_vec

    return l2_normalize_rows(all_vecs)

