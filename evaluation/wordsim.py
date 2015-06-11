"""
A quick and dirty script to evaluate against wordsim-353.
"""
from conceptnet5.util import get_support_data_filename
from conceptnet5.assoc_query import get_assoc_data
from conceptnet5.nodes import normalized_concept_uri
import numpy as np
from scipy.stats import spearmanr

finder, assocw = get_assoc_data('assoc-space-5.4')


def text_to_vector(text):
    return assocw.expanded_vector([(normalized_concept_uri('en', text), 1)])


gold_scores = []
our_scores = []


for line in open(get_support_data_filename('wordsim-353/combined.csv')):
    if line.startswith('Word 1'):
        continue
    term1, term2, sscore = line.split(',')
    gold_score = float(sscore)
    vec1 = text_to_vector(term1)
    vec2 = text_to_vector(term2)
    our_score = vec1.dot(vec2)
    print(term1, term2, gold_score, our_score)
    gold_scores.append(gold_score)
    our_scores.append(our_score)

print()
correlation = spearmanr(np.array(gold_scores), np.array(our_scores))
print("Spearman correlation: %s" % (correlation,))
