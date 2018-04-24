import msgpack
import numpy as np
import pandas as pd
from annoy import AnnoyIndex
from ordered_set import OrderedSet
from sklearn.preprocessing import normalize
from wordfreq import word_frequency

from conceptnet5.language.lemmatize import lemmatize_uri
from conceptnet5.uri import get_uri_language, uri_prefix, uri_to_label
from conceptnet5.vectors import standardized_uri, similar_to_vec, get_vector, cosine_similarity


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
    index = frame.index
    return pd.DataFrame(data=normalize(frame, norm='l1', copy=False, axis=0), index=index)


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
    return pd.DataFrame(data=normalize(frame, norm='l2', copy=False, axis=1), index=index)


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
    for i, item in enumerate(frame.index):
        index.add_item(i, frame.loc[item])
    index.build(tree_depth)
    index_map = OrderedSet(frame.index)
    return index, index_map


def make_replacements_faster(small_frame, big_frame, tree_depth=1000, lang='en', verbose=False):
    """
    Create a replacements dictionary to map terms only present in a big frame to the closest term
    in a small_frame. This is a faster than make_replacements(), because it uses a fast
    implementation of the approximate nearest neighbor algorithm.

    tree_depth=1000 provides a good balance of speed and accuracy.
    """
    intersected = big_frame.reindex(small_frame.index).dropna()
    index, index_map = build_annoy_tree(intersected, tree_depth)
    replacements = {}
    for term in big_frame.index:
        if term not in small_frame.index and not term.startswith('/x/'):
            most_similar_index = index.get_nns_by_vector(big_frame.loc[term], 1)[0]
            most_similar = index_map[most_similar_index]
            similarity = cosine_similarity(get_vector(big_frame, term, lang),
                                           get_vector(small_frame, most_similar, lang))
            replacements[term] = [most_similar, round(similarity, 2)]

            if verbose and not (len(replacements) % 20):
                print('{} ==> {}, {}'.format(term, most_similar, similarity))
    return replacements


def make_replacements(small_frame, big_frame):
    """
    Create a replacements dictionary to map terms only present in a big frame to the closest term
    in a small_frame. This method uses a brute-force solution.
    """
    intersected = big_frame.reindex(small_frame.index).dropna()
    replacements = {}
    for term in big_frame.index:
        if term not in small_frame.index:
            most_similar = similar_to_vec(intersected, big_frame.loc[term], limit=1)
            got = list(most_similar.index)
            if got:
                replacements[term] = got[0]
    return replacements


def choose_small_vocabulary(big_frame, concepts_filename, language):
    """
    Choose the vocabulary of the small frame, by eliminating the terms which:
     - contain more than one word
     - are not in ConceptNet
     - are not frequent
    """
    concepts = set(line.strip() for line in open(concepts_filename))
    vocab = []
    for term in big_frame.index:
        if '_' not in term and term in concepts:
            try:
                frequency = word_frequency(uri_to_label(term), language, wordlist='large')
            except LookupError:
                frequency = word_frequency(uri_to_label(term), language, wordlist='combined')
            vocab.append((term, frequency))
    small_vocab = [term for term, frequency in sorted(vocab, key=lambda x: x[1], reverse=True)[
                                               :50000]]
    return small_vocab


def make_big_frame(frame, language):
    """
     Choose the vocabulary for the big frame and make the big frame. Eliminate the terms which
     are in languages other than the language specified.
    """
    vocabulary = [term for term in frame.index if get_uri_language(term) == language]
    big_frame = frame.ix[vocabulary]
    return big_frame


def make_small_frame(big_frame, concepts_filename, language):
    """
    Create a small frame using the output of choose_small_vocabulary()
    """
    small_vocab = choose_small_vocabulary(big_frame, concepts_filename, language)
    return big_frame.ix[small_vocab]


def save_replacements(output_filepath, replacements):
    # Save the replacement dictionary as a msgpack file
    with open(output_filepath, 'wb') as output_file:
        msgpack.dump(replacements, output_file)
