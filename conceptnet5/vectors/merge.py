# coding: utf-8
import pandas as pd
import numpy as np
from conceptnet5.languages import CORE_LANGUAGES
from conceptnet5.uri import get_language
from .transforms import l2_normalize_rows
from .formats import save_hdf


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
    uframe = pd.DataFrame(U[:, :k], index=frame.index, dtype='f')
    vframe = pd.DataFrame(Vt.T[:, :k], index=frame.columns, dtype='f')
    return uframe, Σ[:k], vframe


def merge_intersect(frames, subsample=20, vocab_cutoff=200000, k=300):
    label_intersection = set(frames[0].index)
    for frame in frames[1:]:
        label_intersection &= set(frame.index)
    filtered_labels = pd.Series(
        [label for label in sorted(label_intersection)
         if '_' not in label and get_language(label) in CORE_LANGUAGES]
    )
    frames = [frame.loc[filtered_labels].astype('f') for frame in frames]
    joined = pd.concat(frames, join='inner', axis=1, ignore_index=True)
    joined.fillna(0.)
    adjusted = l2_normalize_rows(joined.ix[::subsample] - joined.mean(0))

    # Search the frames for significant terms that we've missed.
    # Significant terms are those that appear in 3 different vocabularies,
    # or in 2 different vocabularies and in the first `vocab_cutoff` rows of
    # one of them.

    print('Finding expanded vocabulary')
    vocabulary = frames[0].index
    for frame in frames[1:]:
        vocabulary |= frame.index
    term_scores = pd.Series(index=vocabulary).fillna(0)
    for frame in frames[1:]:
        term_scores.loc[frame.index] += 1
        term_scores.loc[frame.index[:vocab_cutoff]] += 1
    new_terms = vocabulary[term_scores >= 3].difference(joined.index)
    new_vecs = [frame.reindex(new_terms) for frame in frames]

    print('Building input matrix with expanded vocabulary')
    joined2 = pd.concat([
        joined,
        pd.concat(new_vecs, join='outer', axis=1, ignore_index=True).astype('f').fillna(0.)
    ])

    del new_vecs
    projected, eigenvalues, projection = dataframe_svd_projection(adjusted, k)
    del adjusted

    print('Saving results in /tmp')
    del projected

    print('Projecting vocabulary into new space')
    reprojected = joined2.dot(projection)
    reprojected /= (eigenvalues ** .5)
    del joined2
    reprojected = l2_normalize_rows(reprojected, offset=1e-6)
    reprojected.sort_index(inplace=True)
    return reprojected, projection
