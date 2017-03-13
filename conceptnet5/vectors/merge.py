# coding: utf-8
import pandas as pd
import numpy as np
from conceptnet5.uri import split_uri
from conceptnet5.languages import CORE_LANGUAGES
from ..vectors import similar_to_vec, weighted_average
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


def merge_intersect(frames, subsample=20, ranked_frames=2, vocab_cutoff=200000, k=300):
    joined = pd.concat(frames, join='inner', axis=1, ignore_index=True).astype('f')
    joined.fillna(0.)
    filtered_labels = pd.Series([label for label in joined.index if '_' not in label and label.split('/')[2] in CORE_LANGUAGES])
    adjusted = l2_normalize_rows(joined.loc[filtered_labels].ix[::subsample] - joined.mean(0))

    # Search the first `ranked_frames` frames for significant terms that we've
    # missed. Significant terms need to appear in the first `vocab_cutoff` rows
    # of one of the frames.

    print('Finding expanded vocabulary')
    vocabulary = frames[0].index
    for frame in frames[1:ranked_frames]:
        vocabulary |= frame.index
    term_scores = pd.Series(index=vocabulary).fillna(0)
    for frame in frames[:ranked_frames]:
        term_scores.loc[frame.index] += 1
        term_scores.loc[frame.index[:vocab_cutoff]] += 1
    new_terms = vocabulary[term_scores >= 3].difference(joined.index)
    new_vecs = [frame.reindex(new_terms) for frame in frames]

    print('Building input matrix with expanded vocabulary')
    joined2 = pd.concat([
        joined,
        pd.concat(new_vecs, join='outer', axis=1, ignore_index=True).astype('f').fillna(0.)
    ])

    projected, eigenvalues, projection = dataframe_svd_projection(adjusted, k)

    print('Saving results in /tmp')
    save_hdf(projected, '/tmp/u.h5')
    save_hdf(projection, '/tmp/v.h5')

    print('Projecting vocabulary into new space')
    reprojected = l2_normalize_rows(joined2.dot(projection) / (eigenvalues ** .5), offset=1e-6)
    reprojected.sort_index(inplace=True)
    return reprojected, projection
