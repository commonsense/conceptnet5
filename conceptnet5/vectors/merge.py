# coding: utf-8
import pandas as pd
import numpy as np
from conceptnet5.languages import CORE_LANGUAGES
from .transforms import l2_normalize_rows
from sklearn.preprocessing import normalize


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


def concat_intersect(frames):
    frame_col_offsets = [0]
    ncolumns = frames[0].shape[1]
    label_intersection = set(frames[0].index)
    for frame in frames[1:]:
        label_intersection &= set(frame.index)
        frame_col_offsets.append(ncolumns)
        ncolumns += frame.shape[1]
    nrows = len(label_intersection)
    label_intersection = sorted(label_intersection)

    joindata = np.zeros((nrows, ncolumns), 'f')
    for frame, offset in zip(frames, frame_col_offsets):
        width = frame.shape[1]
        joindata[:, offset:(offset + width)] = frame.loc[label_intersection].values
    joined = pd.DataFrame(joindata, index=label_intersection)
    return joined


def concat_union(frames):
    pass


def merge_intersect(frames, subsample=20, vocab_cutoff=200000, k=300):
    joined = concat_intersect(frames)
    filtered_labels = pd.Series([
        label for (i, label) in enumerate(joined.index)
        if i % subsample == 0 and '_' not in label
        and label.split('/')[2] in CORE_LANGUAGES
    ])
    adjusted = joined.loc[filtered_labels]
    adjusted -= joined.mean(0)
    normalize(adjusted.values, norm='l2', copy=False)

    projected, eigenvalues, projection = dataframe_svd_projection(adjusted, k)
    del adjusted
    del projected

    reprojected = joined.dot(projection)
    del joined
    np.divide(reprojected.values, eigenvalues ** .5, out=reprojected.values)
    normalize(reprojected.values, norm='l2', copy=False)
    assert not reprojected.isnull().values.any()
    reprojected.sort_index(inplace=True)
    return reprojected, projection
