from conceptnet5.nodes import standardized_concept_uri
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
    return replace_numbers(standardized_concept_uri(language, term))


def get_vector(frame, text, language=None):
    """
    Returns the row of a vector-space DataFrame `frame` corresponding
    to the text `text`. If `language` is set, this can take in plain text
    and normalize it to ConceptNet form. Either way, it can also take in
    a label that is already in ConceptNet form.
    """
    if language is not None and not text.startswith('/'):
        text = standardized_concept_uri(language, text)
    try:
        return frame.loc[text]
    except KeyError:
        return pd.Series(index=frame.columns)


def normalize_vec(vec):
    return normalize(vec.fillna(0).reshape(1, -1))[0]


def cosine_similarity(vec1, vec2):
    """
    Get the cosine similarity between two vectors -- the cosine of the angle
    between them, ranging from -1 for anti-parallel vectors to 1 for parallel
    vectors.
    """
    return normalize_vec(vec1).dot(normalize_vec(vec2))


def similar_to(frame, text, num=50, language=None):
    """
    Returns a sorted Series of the items with vectors most similar to `text`.
    """
    vec = get_vector(frame, text, language)
    return similar_to_vec(frame, vec)


def similar_to_vec(frame, vec, num=50):
    similarity = frame.dot(vec).sort(ascending=False, inplace=False)
    if num is not None:
        similarity = similarity.iloc[0:num]
    return similarity.dropna()


def get_similarity(frame, text1, text2, language=None):
    vec1 = get_vector(frame, text1, language)
    vec2 = get_vector(frame, text2, language)
    return cosine_similarity(vec1, vec2)


def weighted_average(frame, weight_series):
    vec = pd.Series(index=frame.columns, dtype='f')

    for label in weight_series.index:
        if label in frame.index:
            val = weight_series.loc[label]
            vec += val * frame.loc[label]

    return vec
