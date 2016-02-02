from conceptnet5.util import get_data_filename, get_support_data_filename
from conceptnet5.vectors import get_vector, get_similarity
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def read_ws353():
    """
    Parses the word-similarity 353 test collection (ws353). ws353 is a
    collection of 353 english word pairs, each with a relatedness rating between
    0 (totally unrelated) to 10 (very related or identical). The relatedness
    of a pair of words was determined by the average scores of either 13
    or 16 native english speakers.
    """
    with open(get_support_data_filename('wordsim-353/combined.csv')) as file:
        for line in file:
            if line.startswith('Word 1'): # Skip the header
                continue
            term1, term2, sscore = line.split(',')
            gold_score = float(sscore)
            yield term1, term2, gold_score


def read_men3000(subset='dev'):
    """
    Parses the MEN test collection. MEN is a collection of 3000 english word
    pairs, each with a relatedness rating between 0 and 50. The relatedness of
    a pair of words was determined by the number of times the pair was selected
    as more related compared to another randomly chosen pair.
    """
    filename = get_support_data_filename('mensim/MEN_dataset_lemma_form.{}'.format(subset))
    with open(filename) as file:
        for line in file:
            parts = line.rstrip().split()
            term1 = parts[0].split('-')[0]  # remove part of speech
            term2 = parts[1].split('-')[0]
            gold_score = float(parts[2])
            yield term1, term2, gold_score


def read_rg65():
    """
    Parses the Rubenstein and Goodenough word similarity test collection.
    """
    filename = get_support_data_filename('rg65/EN-RG-65.txt')
    with open(filename) as file:
        for line in file:
            parts = line.split()
            yield parts[0], parts[1], float(parts[2])


def read_rw(subset='dev'):
    """
    Parses the rare word similarity test collection.
    """
    filename = get_support_data_filename('rw/rw-{}.csv'.format(subset))
    with open(filename) as file:
        for line in file:
            parts = line.split()
            yield parts[0], parts[1], float(parts[2])


def read_mc():
    """
    Parses the Miller and Charles word similarity test collection.
    """
    filename = get_support_data_filename('mc/EN-MC-30.txt')
    with open(filename) as file:
        for line in file:
            parts = line.split()
            yield parts[0], parts[1], float(parts[2])


def spearman_evaluate(frame, standard, language='en', verbose=2):
    """
    Tests assoc_space's ability to recognize word correlation. This function
    computes the spearman correlation between assoc_space's reported word
    correlation and the expected word correlation according to 'standard'.
    """
    gold_scores = []
    our_scores = []

    for term1, term2, gold_score in standard:
        our_score = get_similarity(frame, term1, term2, language)
        if verbose > 1:
            print('%s\t%s\t%3.3f\t%3.3f' % (term1, term2, gold_score, our_score))
        gold_scores.append(gold_score)
        our_scores.append(our_score)

    correlation = spearmanr(np.array(gold_scores), np.array(our_scores))[0]

    if verbose:
        print("Spearman correlation: %s" % (correlation,))

    return correlation


def evaluate(frame, subset='dev'):
    men_score = spearman_evaluate(frame, read_men3000(subset))
    rw_score = spearman_evaluate(frame, read_rw(subset))
    ws_score = spearman_evaluate(frame, read_ws353())
    results = pd.Series([men_score, rw_score, ws_score], index=['men3000', 'rw', 'ws353'])
    return results
