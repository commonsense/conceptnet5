import pandas as pd
import numpy as np
import wordfreq
from ..vectors import standardized_uri, similar_to_vec
from conceptnet5.uri import uri_prefix, split_uri
from conceptnet5.language.lemmatize import lemmatize_uri
from conceptnet5.languages import CORE_LANGUAGES


def standardize_row_labels(frame, language='en', forms=True):
    """
    Convert a frame whose row labels are bare English terms to one whose row
    labels are standardized ConceptNet URIs (with some extra word2vec-style
    normalization of digits). Rows whose labels get the same
    standardized URI get combined, with earlier rows given more weight.
    """
    # Re-label the DataFrame with standardized, non-unique row labels
    frame.index = [uri_prefix(standardized_uri(language, label)) for label in frame.index]

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
    combined_weights.sort(ascending=False)
    result = scaled.loc[combined_weights.index]
    return result


def l1_normalize_columns(frame):
    """
    L_1-normalize the columns of this DataFrame, so that the absolute values of
    each column's entries add up to 1. This is particularly helpful when
    post-processing GloVe output.
    """
    col_norms = np.sum(np.abs(frame), axis='rows')
    return frame.div(col_norms, axis='columns')


def l2_normalize_rows(frame, offset=0.):
    """
    L_2-normalize the rows of this DataFrame, so their lengths in Euclidean
    distance are all 1. This enables cosine similarities to be computed as
    dot-products between these rows.

    Zero-rows will end up normalized to NaN, but that is actually the
    Pandas-approved way to represent missing data, so Pandas should be able to
    deal with those.
    """
    row_norms = np.sqrt(np.sum(np.power(frame, 2), axis='columns')) + offset
    return frame.div(row_norms, axis='rows')


def shrink_and_sort(frame, n, k):
    """
    Truncate a matrix to NxK, re-normalize it, and arrange the rows in
    lexicographic order for querying.
    """
    shrunk = l2_normalize_rows(frame.iloc[:n, :k])
    shrunk.sort_index(inplace=True)
    return shrunk


def term_freq(term):
    _c, lang, term = split_uri(term)[:3]
    if lang == 'en':
        return wordfreq.word_frequency(term, 'en', 'large')
    elif lang in CORE_LANGUAGES:
        return wordfreq.word_frequency(term, lang)
    else:
        return 0.


def miniaturize(frame, prefix='/c/', other_vocab=None, k=256):
    """
    Produce a small matrix with good coverage of English and reasonable
    coverage of the other 'core languages' in ConceptNet. A `prefix` can be
    provided to limit the result to one language.
    """
    vocab1 = [term for term in frame.index if '_' not in term
              and term.startswith(prefix) and term_freq(term) > 0.]
    vocab_set = set(vocab1)
    if other_vocab is not None:
        extra_vocab = [term for term in other_vocab if '_' in term and
                       term in frame.index and term not in vocab_set]
        extra_vocab = extra_vocab[:20000]
    else:
        extra_vocab = []

    vocab = vocab1 + extra_vocab
    smaller = frame.loc[vocab]
    U, _S, _Vt = np.linalg.svd(smaller, full_matrices=False)
    redecomposed = l2_normalize_rows(pd.DataFrame(U[:, :k], index=vocab, dtype='f'))
    mini = (redecomposed * 64).astype(np.int8)
    mini.sort_index(inplace=True)
    return mini


def make_replacements(small_frame, big_frame, limit=100000):
    intersected = big_frame.loc[small_frame.index].dropna()
    replacements = {}
    for term in big_frame.index:
        if term not in small_frame.index:
            most_similar = similar_to_vec(intersected, big_frame.loc[term], limit=1)
            got = list(most_similar.index)
            if got:
                replacements[term] = got[0]
    return replacements
