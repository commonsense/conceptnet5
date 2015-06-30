from conceptnet5.util import get_data_filename, get_support_data_filename
from assoc_space import AssocSpace
from assoc_space.eigenmath import normalize
from conceptnet5.nodes import normalized_concept_uri
import numpy as np
from scipy.stats import spearmanr

def text_to_vector(text, assoc):
    uri = normalized_concept_uri('en', text)
    return assoc.vector_from_terms([(uri, 1.)])

def cos_diff(a, b):
    return normalize(a).dot(normalize(b))

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
    Parses the MEN test collection. MEN is a collection of 3000 english word
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

def read_rg65():
    """
    Parses the Rubenstein and Goodenough word similarity test collection.
    """
    filename = get_support_data_filename('rg65/EN-RG-65.txt')
    with open(filename) as file:
        for line in file:
            parts = line.split()
            yield parts[0], parts[1], float(parts[2])

def read_rw():
    """
    Parses the rare word similarity test collection.
    """
    filename = get_support_data_filename('rw/rw.txt')
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

def spearman_evaluate(standard, assoc, verbose=1):
    """
    Tests assoc_space's ability to recognize word correlation. This function
    computes the spearman correlation between assoc_space's reported word
    correlation and the expected word correlation according to 'standard'.
    """
    gold_scores = []
    our_scores = []

    for term1, term2, gold_score in standard:
        vec1 = text_to_vector(term1, assoc)
        vec2 = text_to_vector(term2, assoc)
        our_score = cos_diff(vec1, vec2)
        if verbose > 1:
            print(term1, term2, gold_score, our_score)
        gold_scores.append(gold_score)
        our_scores.append(our_score)

    correlation = spearmanr(np.array(gold_scores), np.array(our_scores))[0]

    if verbose:
        print("Spearman correlation: %s" % (correlation,))

    return correlation

def test(assoc):
    print("ws353")
    ws353 = spearman_evaluate(read_ws353(), assoc)
    print("men3000")
    men3000 = spearman_evaluate(read_men3000(), assoc)
    print("rg65")
    rg65 = spearman_evaluate(read_rg65(), assoc)
    print("rw")
    rw = spearman_evaluate(read_rw(), assoc)
    print("mc")
    mc = spearman_evaluate(read_mc(), assoc)

def main(dir):
    assoc = AssocSpace.load_dir(dir)
    test(assoc)

if __name__ == '__main__':
    import sys
    main(sys.argv[1])
