import numpy as np
from scipy import sparse

from wordfreq import word_frequency
from ftfy import fix_text

from assoc_space import AssocSpace, LabelSet
from assoc_space.eigenmath import normalize_rows

from conceptnet5.nodes import normalized_concept_uri
from conceptnet5.util import get_data_filename
# FIXME: negate_concept should live somewhere nicer
from conceptnet5.builders.assoc_to_vector_space import negate_concept

from collections import defaultdict
import pathlib


def conceptnet_normalizer(text):
    """
    Normalizes a text into a concept URI. This function assume the text is
    english.
    """
    return normalized_concept_uri('en', text)

def load_glove_vectors(filename, labels, filter_beyond_row=250000,
                        end_row=1000000, frequency_cutoff=1e-6):
    """
    Loads glove vectors from a file and returns a list of numpy arrays.

    Each line of the file contains a word and a space separated vector. The
    lines are sorted by word frequency.

    This function will only parse at most `end_row` lines.

    If the index of a line is greater than `filter_beyond_row` and its
    frequency according to wordfreq is less than `frequency_cutoff`, it is
    ignored.
    """
    vectors = []
    with open(filename, encoding='latin-1') as file:
        for i, line in enumerate(file):
            if i >= end_row:
                break

            parts = line.rstrip().split(' ')
            ctext = fix_text(parts[0]).replace('\n', '').strip()
            concept = conceptnet_normalizer(ctext)

            if i >= filter_beyond_row and \
                word_frequency(ctext, 'en') < frequency_cutoff:
                continue

            index = labels.add(concept)

            #We extend `vectors` to the appropriate length
            while index >= len(vectors):
                vectors.append(np.zeros(len(parts)-1))

            # We need to combine words with the same normalization, but
            # different raw forms. We approximate this according to zipf's law
            zipf_weight = 1 / (i + 1)
            vec = np.array([float(part) for part in parts[1:]])
            vectors[index] += vec * zipf_weight

    return vectors


def make_sparse_assoc(filename, labels, verbose=True):
    """
    Generates a sparse association matrix from a file. The entries correspond
    to the existing entries in labels. Concepts not in labels are ignored.
    """
    # We ignore the concepts not in the labels so we can perform matrix
    # multiplication between the sparse matrix and the word vectors

    mat = sparse.csr_matrix((len(labels), len(labels), dtype=float))

    if verbose:
        print("Loading sparse associations")

    # Add pairwise associations
    with open(filename, encoding='utf-8') as infile:
        for line in infile:
            line = line.rstrip()
            concept1, concept2, value_str = line.split('\t')
            if concept1 in labels and concept2 in labels:
                index1 = labels.index(concept1)
                index2 = labels.index(concept2)
                value = float(value_str)

                mat[index1, index2] = value
                mat[index2, index1] = value
    if verbose:
        print("Adding self-loops and negations")

    # A concept is very related to itself
    for index, row in mat:

        mat[index, index] = np.sum(row) + 10 #TODO Why 10?

        # A concept is unrelated to its negation
        neg = negate_concept(concept)

        if neg in labels:
            mat(index, labels.index(neg)) = -0.5 #TODO Why -0.5?

    if verbose:
        print("Building sparse matrix")

        return mat


def retrofit(dense_file, sparse_file, output_file,
        iterations=10, offset=1e-9, verbose=True):
    """
    Updates the word vectors contained in `dense_file` using the association
    contained in `sparse_file` and writes the new vectors to `output_file`.

    The function will apply retrofitting `iterations` times.

    A larger `offset` causes vectors with small magnitudes to be normalized
    into vectors with magnitudes less than 1.
    """
    labels = LabelSet()
    vectors = load_glove_vectors(dense_file, labels)
    sparse_csr = make_sparse_assoc(sparse_file, labels)

    if verbose:
        print("Building dense matrix")

    orig_dense = normalize_rows(np.array(vectors), offset=offset)
    dense = np.copy(orig_dense)

    if verbose:
        print("Retrofitting")

    for iter in range(iterations):
        if verbose:
            print("%d/10" % (iter + 1))

        newdense = normalize_rows(sparse_csr.dot(dense), offset)
        newdense += orig_dense
        newdense /= 2
        dense = newdense

        if verbose:
            print("Average diff: %s" % np.mean(np.abs(dense - orig_dense)))

    assoc = AssocSpace(dense, np.ones(len(vectors[0])), labels, assoc=dense)
    assoc.save_dir(output_file)

def main():
    import sys
    retrofit(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == '__main__':
    main()
