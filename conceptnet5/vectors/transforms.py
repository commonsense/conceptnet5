import pandas as pd
import numpy as np
from annoy import AnnoyIndex
import msgpack

from ..vectors import standardized_uri, similar_to_vec
from conceptnet5.uri import uri_prefix, get_language
from conceptnet5.language.lemmatize import lemmatize_uri
from conceptnet5.db.query import AssertionFinder


def standardize_row_labels(frame, language='en', forms=True):
    """
    Convert a frame whose row labels are bare English terms (e.g. of the
    form 'en/term') to one whose row labels are standardized ConceptNet URIs
    (e.g. of the form '/c/en/term'; and with some extra word2vec-style
    normalization of digits). Rows whose labels get the same standardized
    URI get combined, with earlier rows given more weight.
    """
    # Check for en/term format we use to train fastText on OpenSubtitles data
    if all(label.count('/') == 1 for label in frame.index[10:20]):
        tuples = [label.partition('/') for label in frame.index]
        frame.index = [uri_prefix(standardized_uri(language, text))
                       for language, _slash, text in tuples]

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
    combined_weights.sort_values(inplace=True, ascending=False)
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


def build_annoy_tree(frame, tree_depth):
    """
    Build a tree to hold a frame's vectors for efficient lookup.
    """
    index = AnnoyIndex(frame.shape[1], metric='euclidean')
    index_map = {}
    for i, item in enumerate(frame.index):
        index.add_item(i, frame.loc[item])
        index_map[i] = item
    index.build(tree_depth)
    return index, index_map


def make_replacements(small_frame, big_frame, tree_depth):
    """
    Create a replacements dictionary to map terms only present in a big frame to the closest term
    in a small_frame
    """
    intersected = big_frame.loc[small_frame.index].dropna()
    index, index_map = build_annoy_tree(intersected, tree_depth)
    replacements = {}
    average_similarity = []
    for term in big_frame.index:
        if term not in small_frame.index:
            indices, scores = index.get_nns_by_vector(big_frame.loc[term], 2,
                                                   include_distances=True)
            i = 0
            if index_map[indices[-1]] != term:
                i = -1
            else:
                i = -2

            replacements[term] = index_map[indices[i]]
            average_similarity.append(scores[i])
    print(np.mean(average_similarity))
    return replacements


def choose_small_vocabulary(big_frame, lang):
    """
    Choose the vocabulary of the small frame, by eliminating the terms which:
     - are in a languages other than a lang specified with a lang parameter.
     - contain more than one word
     - are not in ConceptNet
    """
    small_vocabulary = []
    finder = AssertionFinder()

    for term in big_frame.index:
        # Check if a term is in the language of choice
        if get_language(term) == lang:

            # Make sure the term is not a phrase
            if term.count('_') < 1:

                # Check if a term comes from ConceptNet, not Glove or Word2Vec
                results = finder.lookup(term)
                if results:
                    small_vocabulary.append(term)
    return small_vocabulary


def make_big_frame(frame, lang):
    vocabulary = []
    for term in frame.index:
        if get_language(term) == lang:
            vocabulary.append(term)
    big_frame = frame.ix[vocabulary]
    return big_frame


def make_small_frame(big_frame, language):
    """
    Create a small frame using the output of choose_small_vocabulary()
    """
    small_vocab = choose_small_vocabulary(big_frame, language)
    return big_frame.ix[small_vocab]


def save_replacements(output_filepath, replacements):
    # Save the replacement dictionary as a mgspack file
    with open(output_filepath, 'wb') as output_file:
        msgpack.dump(replacements, output_file)


def save_small_frame(output_filepath, small_frame):
    # Save the small frame as hdfs
    small_frame.to_hdf(output_filepath, 'mat', encoding='utf-8')
