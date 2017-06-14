import random
from os.path import join

import click
import msgpack
import numpy as np
import pandas as pd
from annoy import AnnoyIndex

from conceptnet5.db.query import AssertionFinder
from conceptnet5.language.lemmatize import lemmatize_uri
from conceptnet5.uri import uri_prefix, get_language
from conceptnet5.vectors import standardized_uri, similar_to_vec


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


def make_replacements_faster(small_frame, big_frame, tree_depth=1000, verbose=False):
    """
    Create a replacements dictionary to map terms only present in a big frame to the closest term
    in a small_frame. This is a faster than make_replacements(), because it uses a fast
    implementation of the approximate nearest neighbor algorithm.

    tree_depth=1000 provides a good balance of speed and accuracy.
    """
    intersected = big_frame.loc[small_frame.index].dropna()
    index, index_map = build_annoy_tree(intersected, tree_depth)
    replacements = {}
    for term in big_frame.index:
        if term not in small_frame.index:
            most_similar = index.get_nns_by_vector(big_frame.loc[term], 1)[0]
            replacements[term] = index_map[most_similar]

    if verbose:
        random.seed(20)
        for replacement_pair in random.sample(replacements.items(), 50):
            print(replacement_pair)
    return replacements


def make_replacements(small_frame, big_frame):
    """
    Create a replacements dictionary to map terms only present in a big frame to the closest term
    in a small_frame. This method uses a brute-force solution.
    """
    intersected = big_frame.loc[small_frame.index].dropna()
    replacements = {}
    for term in big_frame.index:
        if term not in small_frame.index:
            most_similar = similar_to_vec(intersected, big_frame.loc[term], limit=1)
            got = list(most_similar.index)
            if got:
                replacements[term] = got[0]
    return replacements


def choose_small_vocabulary(big_frame):
    """
    Choose the vocabulary of the small frame, by eliminating the terms which:
     - contain more than one word
     - are not in ConceptNet
    """
    small_vocabulary = []
    finder = AssertionFinder()

    for term in big_frame.index:
        # Make sure the term is not a phrase
        if term.count('_') < 1:
            # Check if a term comes from ConceptNet
            results = finder.lookup(term)
            if results:
                small_vocabulary.append(term)
    return small_vocabulary


def make_big_frame(frame, lang):
    """
     Choose the vocabulary for the big frame and make the big frame. Eliminate the terms which
     are in languages other than the language specified with the lang parameter.
    """
    vocabulary = []
    for term in frame.index:
        if get_language(term) == lang:
            vocabulary.append(term)
    big_frame = frame.ix[vocabulary]
    return big_frame


def make_small_frame(big_frame):
    """
    Create a small frame using the output of choose_small_vocabulary()
    """
    small_vocab = choose_small_vocabulary(big_frame)
    return big_frame.ix[small_vocab]


def save_replacements(output_filepath, replacements):
    # Save the replacement dictionary as a mgspack file
    with open(output_filepath, 'wb') as output_file:
        msgpack.dump(replacements, output_file)


def save_frame(output_filepath, frame):
    frame.to_hdf(output_filepath, 'mat', encoding='utf-8')


@click.command()
@click.argument('frame-filepath')
@click.argument('output-dir')
@click.option('--lang', default='en')
@click.option('--tree-depth', default=1000)
@click.option('-v', '--verbose', is_flag=True)
def make_save_replacements(frame_filepath, output_dir, lang, tree_depth, verbose):
    frame = pd.read_hdf(frame_filepath, 'mat', encoding='utf-8')
    big_frame = make_big_frame(frame, lang)
    small_frame = make_small_frame(big_frame)
    replacements = make_replacements_faster(small_frame, big_frame, tree_depth, verbose)
    save_replacements(join(output_dir, '{}_replacements.msgpack'.format(lang)), replacements)
    save_frame(join(output_dir, '{}_big_frame.h5'.format(lang)), big_frame)
    save_frame(join(output_dir, '{}_small_frame.h5'.format(lang)), small_frame)

if __name__ == '__main__':
    make_save_replacements()
