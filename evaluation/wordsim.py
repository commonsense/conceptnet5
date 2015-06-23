"""
A quick and dirty script to evaluate against wordsim-353.
"""
from conceptnet5.util import get_support_data_filename
from conceptnet5.assoc_query import get_assoc_data
from conceptnet5.nodes import normalized_concept_uri
import numpy as np
from assoc_space.eigenmath import normalize
from scipy.stats import spearmanr

finder, assocw = get_assoc_data('assoc-space-5.4')


def text_to_vector(text):
    return assocw.expanded_vector([(normalized_concept_uri('en', text), 1)])


gold_scores = []
our_scores = []


def read_ws353():
    for line in open(get_support_data_filename('wordsim-353/combined.csv')):
        if line.startswith('Word 1'):
            continue
        term1, term2, sscore = line.split(',')
        gold_score = float(sscore)
        yield term1, term2, gold_score


def read_men3000():
    for line in open(get_support_data_filename('mensim/MEN_dataset_lemma_form.dev')):
        parts = line.rstrip().split()
        term1 = parts[0].split('-')[0]
        term2 = parts[1].split('-')[0]
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
