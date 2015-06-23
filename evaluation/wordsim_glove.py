"""
A quick and dirty script to evaluate against wordsim-353.
"""
from conceptnet5.util import get_data_filename, get_support_data_filename
from assoc_space import AssocSpace
from assoc_space.eigenmath import normalize
from conceptnet5.nodes import normalized_concept_uri
import numpy as np
from scipy.stats import spearmanr

assoc = AssocSpace.load_dir(get_data_filename('assoc/glove.retrofit'))

def text_to_vector(text):
    uri = normalized_concept_uri('en', text)
    return normalize(assoc.vector_from_terms([(uri, 1.)]))


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


def read_men3000():
    """
    Parsers the MEN test collection. MEN is a collection of 3000 english word
    pairs, each with a relatedness rating between 0 and 50. The relatedness of
    a pair of words was determined by the number of times the pair was selected
    as more related compared to another randomly chosen pair.
    """
    filename = get_support_data_filename('mensim/MEN_dataset_lemma_form.dev')
    with open(filename) as file:
        for line in file:
            parts = line.rstrip().split()
            term1 = parts[0].split('-')[0] # remove part of speech
            term2 = parts[1].split('-')[0] # as above
            gold_score = float(parts[2])
            yield term1, term2, gold_score


def spearman_evaluate(standard):
    gold_scores = []
    our_scores = []

    for term1, term2, gold_score in standard:
        vec1 = text_to_vector(term1)
        vec2 = text_to_vector(term2)
        our_score = vec1.dot(vec2)
        print(term1, term2, gold_score, our_score)
        gold_scores.append(gold_score)
        our_scores.append(our_score)

    print()
    correlation = spearmanr(np.array(gold_scores), np.array(our_scores))[0]
    print("Spearman correlation: %s" % (correlation,))
    print()
    return correlation


spearman_evaluate(read_ws353())
spearman_evaluate(read_men3000())
