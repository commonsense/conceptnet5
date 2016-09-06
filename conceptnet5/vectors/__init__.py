from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.language.lemmatize import lemmatize_uri
from sklearn.preprocessing import normalize
import re
import pandas as pd
import numpy as np


DOUBLE_DIGIT_RE = re.compile(r'[0-9][0-9]')
DIGIT_RE = re.compile(r'[0-9]')


def replace_numbers(s):
    """
    Replace digits with # in any term where a sequence of two digits appears.

    This operation is applied to text that passes through word2vec, so we
    should match it.
    """
    if DOUBLE_DIGIT_RE.search(s):
        return DIGIT_RE.sub('#', s)
    else:
        return s


def standardized_uri(language, term):
    """
    Get a URI that is suitable to label a row of a vector space, by making sure
    that both ConceptNet's and word2vec's normalizations are applied to it.

    If the term already looks like a ConceptNet URI, it will only have its
    sequences of digits replaced by #. Otherwise, it will be turned into a
    ConceptNet URI in the given language, and then have its sequences of digits
    replaced.
    """
    if not (term.startswith('/') and term.count('/') >= 2):
        term = standardized_concept_uri(language, term)
    return replace_numbers(term)


def get_vector(frame, label, language=None):
    """
    Returns the row of a vector-space DataFrame `frame` corresponding
    to the text `text`. If `language` is set, this can take in plain text
    and normalize it to ConceptNet form. Either way, it can also take in
    a label that is already in ConceptNet form.
    """
    if language is not None and not label.startswith('/'):
        label = standardized_uri(language, label)
    try:
        return frame.loc[label]
    except KeyError:
        return pd.Series(index=frame.columns)


def normalize_vec(vec):
    """
    Normalize a single vector, as a 1-D ndarray or a Series.
    """
    if isinstance(vec, pd.Series):
        return normalize(vec.fillna(0).reshape(1, -1))[0]
    elif isinstance(vec, np.ndarray):
        return normalize(vec.reshape(1, -1))[0]
    else:
        raise TypeError(vec)


def cosine_similarity(vec1, vec2):
    """
    Get the cosine similarity between two vectors -- the cosine of the angle
    between them, ranging from -1 for anti-parallel vectors to 1 for parallel
    vectors.
    """
    return normalize_vec(vec1).dot(normalize_vec(vec2))


def similar_to_vec(frame, vec, limit=50):
    if vec.dot(vec) == 0.:
        return pd.Series(data=[], index=[], dtype='f')
    similarity = frame.dot(vec)
    return similarity.dropna().nlargest(limit)


def weighted_average(frame, weight_series):
    if isinstance(weight_series, list):
        weight_dict = dict(weight_series)
        weight_series = pd.Series(weight_dict)
    vec = np.zeros(frame.shape[1], dtype='f')

    for label in weight_series.index:
        if label in frame.index:
            val = weight_series.loc[label]
            vec += val * frame.loc[label].values

    return pd.Series(data=vec, index=frame.columns, dtype='f')
