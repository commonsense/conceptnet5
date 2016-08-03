# coding: utf-8
import pandas as pd
import numpy as np
import wordfreq
from conceptnet5.uri import split_uri
from ..vectors import similar_to_vec, weighted_average
from .transforms import l2_normalize_rows


WORDFREQ_LANGUAGES = set(wordfreq.available_languages())
WORDFREQ_LANGUAGES_LARGE = set(wordfreq.available_languages('large'))


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


def estimate_frequency(term, frame1, frame2, extra_labels):
    freq = 0.
    _c, lang, text = split_uri(term)[:3]

    # Add the word frequency from wordfreq, if we can
    if '_' not in text and lang in WORDFREQ_LANGUAGES:
        if lang in WORDFREQ_LANGUAGES_LARGE:
            freq += wordfreq.word_frequency(text, lang, 'large')
        else:
            freq += wordfreq.word_frequency(text, lang)

    # Guess a frequency from the two frames using Zipf's law
    if term in frame1.index:
        freq += 1.0 / (1. + frame1.index.get_loc(term))
    if term in frame2.index:
        freq += 1.0 / (1. + frame2.index.get_loc(term))
    if term in extra_labels:
        freq *= 2
    return freq


def merge_intersect(frames, small_k=300):
    vocab_intersection = frames[0].index
    big_k = frames[0].shape[1]
    for frame in frames[1:]:
        vocab_intersection &= frame.index
        big_k += frame.shape[1]

    shared_vecs = pd.DataFrame(index=vocab_intersection, columns=range(big_k), dtype='f')
    offset = 0
    for frame in frames:
        k = frame.shape[1]
        shared_vecs.loc[vocab_intersection, offset:offset + k - 1] = frame.loc[vocab_intersection]
        offset += k

    print(shared_vecs.shape)
    projected, projection = dataframe_svd_projection(shared_vecs, small_k)
    return projected, projection



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
    projected, projection = dataframe_svd_projection(shared_vecs, k1 + k2)

    # Select the vectors for sufficiently common words, which will be used as
    # the reference points.
    reference_vecs = pd.DataFrame(projected.loc[common_vocab])
    # Get a truncation of the reference_vecs matrix so we can make quick,
    # sloppy comparisons. Again, indices of a DataFrame are inclusive, so 0:199
    # is the first 200 columns.
    reference_vecs_small = pd.DataFrame(reference_vecs.ix[:, 0:199])

    # Build a matrix that will contain our final term vectors. We already know
    # the vectors for terms that appear in both vocabularies, because they're the
    # rows of `projected`, so we'll assign those to start.
    all_vecs = pd.DataFrame(index=full_labels, columns=range(k1 + k2), dtype='f')
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
        # this is a NumPy array, so endpoints are exclusive
        query_vec_small = query_vec[:200]

        # Get some similar common terms
        most_similar_sloppy = similar_to_vec(reference_vecs_small, query_vec_small, limit=50)
        most_similar = similar_to_vec(reference_vecs.loc[most_similar_sloppy.index], query_vec, limit=5)
        if verbose:
            similar_list = ', '.join(most_similar.index)
            print("%s => %s" % (label, similar_list))

        # Our new interpolated vector is the weighted average of the vectors
        # for these similar terms, weighted by how similar they are.
        interpolated_vec = weighted_average(reference_vecs, most_similar)
        all_vecs.loc[label] = interpolated_vec

    freqs = np.array([
        estimate_frequency(label, frame1, frame2, extra_labels)
        for label in full_labels
    ])
    reordered = np.argsort(-freqs)

    # Truncate the columns of the matrix, as it saves memory in later steps
    # and doesn't cost much performance after this
    return l2_normalize_rows(all_vecs.iloc[reordered, :k1])
