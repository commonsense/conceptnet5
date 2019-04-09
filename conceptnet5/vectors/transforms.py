import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from conceptnet5.language.lemmatize import lemmatize_uri
from conceptnet5.uri import get_uri_language, uri_prefix
from conceptnet5.vectors import standardized_uri


def standardize_row_labels(frame, language='en', forms=True):
    """
    Convert a frame whose row labels are bare English terms (e.g. of the
    form 'en/term') to one whose row labels are standardized ConceptNet URIs
    (e.g. of the form '/c/en/term'; and with some extra word2vec-style
    normalization of digits). Rows whose labels get the same standardized
    URI get combined, with earlier rows given more weight.
    """
    # Check for en/term format we use to train fastText on OpenSubtitles data
    if all(label.count('/') == 1 for label in frame.index[0:5]):
        tuples = [label.partition('/') for label in frame.index]
        frame.index = [
            uri_prefix(standardized_uri(language, text))
            for language, _slash, text in tuples
        ]

    # Re-label the DataFrame with standardized, non-unique row labels
    frame.index = [
        uri_prefix(standardized_uri(language, label)) for label in frame.index
    ]

    # Assign row n a weight of 1/(n+1) for weighted averaging
    nrows = frame.shape[0]
    weights = 1.0 / np.arange(1, nrows + 1)
    label_weights = pd.Series(weights, index=frame.index)

    # groupby(level=0).sum() means to add rows that have the same label
    relabeled = frame.mul(weights, axis='rows').sort_index().groupby(level=0).sum()
    combined_weights = label_weights.sort_index().groupby(level=0).sum()

    # Optionally adjust words to be more like their word forms
    if forms:
        for label in relabeled.index:
            lemmatized = lemmatize_uri(label)
            if lemmatized != label and lemmatized in relabeled.index:
                relabeled.loc[lemmatized] += relabeled.loc[label] / 2
                combined_weights.loc[lemmatized] += combined_weights.loc[label] / 2

    scaled = relabeled.div(combined_weights, axis='rows')

    # Rearrange the items in descending order of weight, similar to the order
    # we get them in from word2vec and GloVe
    combined_weights.sort_values(inplace=True, ascending=False)
    result = scaled.loc[combined_weights.index]
    return result


def l1_normalize_columns(frame):
    """
    L_1-normalize the columns of this DataFrame, so that the absolute values of
    each column's entries add up to 1. This is particularly helpful when
    post-processing GloVe output.
    """
    index = frame.index
    return pd.DataFrame(
        data=normalize(frame, norm='l1', copy=False, axis=0), index=index
    )


def l2_normalize_rows(frame):
    """
    L_2-normalize the rows of this DataFrame, so their lengths in Euclidean
    distance are all 1. This enables cosine similarities to be computed as
    dot-products between these rows.

    Rows of zeroes will be normalized to zeroes, and frames with no rows will
    be returned as-is.
    """
    if frame.shape[0] == 0:
        return frame
    index = frame.index
    return pd.DataFrame(
        data=normalize(frame, norm='l2', copy=False, axis=1), index=index
    )


def subtract_mean_vector(frame):
    """
    Re-center the vectors in a DataFrame by subtracting the mean vector from
    each row.
    """
    return frame.sub(frame.mean(axis='rows'), axis='columns')


def shrink_and_sort(frame, n, k):
    """
    Truncate a DataFrame to NxK, re-normalize it, and arrange the rows in
    lexicographic order for querying.
    """
    shrunk = l2_normalize_rows(frame.iloc[:n, :k])
    shrunk.sort_index(inplace=True)
    return shrunk


def choose_small_vocabulary(index, concepts):
    """
    Choose the vocabulary of the small frame, by eliminating the terms which:
     - contain more than one word
     - are not in ConceptNet
    """
    vocab = [term for term in index if '_' not in term and term in concepts]
    return vocab


def make_big_frame(frame, language):
    """
     Choose the vocabulary for the big frame and make the big frame. Eliminate the terms which
     are in languages other than the language specified.
    """
    vocabulary = [term for term in frame.index if get_uri_language(term) == language]
    big_frame = frame.ix[vocabulary]
    return big_frame


def make_small_frame(big_frame, concepts):
    """
    Create a small frame using the output of choose_small_vocabulary()
    """
    small_vocab = choose_small_vocabulary(big_frame.index, concepts)
    return big_frame.ix[small_vocab]
