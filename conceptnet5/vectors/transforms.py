import pandas as pd
import numpy as np
from .standardize import standardized_uri


def standardize_row_labels(frame, language='en'):
    """
    Convert a frame whose row labels are bare English terms to one whose row
    labels are standardized ConceptNet URIs (with some extra word2vec-style
    normalization of digits). Rows whose labels get the same
    standardized URI get combined, with earlier rows given more weight.
    """
    # Re-label the DataFrame with standardized, non-unique row labels
    frame.index = pd.Series(
        [standardized_uri(language, label) for label in frame.index],
        name='term'
    )

    # Assign row n a weight of 1/(n+1) for weighted averaging
    nrows = frame.shape[0]
    weights = 1.0 / np.arange(1, nrows + 1)
    label_weights = pd.Series(weights, index=frame.index)

    # groupby(level=0).sum() means to add rows that have the same label
    relabeled = frame.mul(weights, axis='rows').sort_index().groupby(level=0).sum()
    combined_weights = label_weights.sort_index().groupby(level=0).sum()
    return relabeled.div(combined_weights, axis='rows')


def l1_normalize_columns(frame):
    """
    L_1-normalize the columns of this DataFrame, so that the absolute values of
    each column's entries add up to 1. This is particularly helpful when
    post-processing GloVe output.
    """
    col_norms = np.sum(np.abs(frame), axis='rows')
    return frame.div(col_norms, axis='columns')


def l2_normalize_rows(frame):
    """
    L_2-normalize the rows of this DataFrame, so their lengths in Euclidean
    distance are all 1. This enables cosine similarities to be computed as
    dot-products between these rows.

    Zero-rows will end up normalized to NaN, but that is actually the
    Pandas-approved way to represent missing data, so Pandas should be able to
    deal with those.
    """
    row_norms = np.sqrt(np.sum(np.power(frame, 2), axis='columns'))
    return frame.div(row_norms, axis='rows')

