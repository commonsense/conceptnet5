import numpy as np
from scipy import sparse

from wordfreq.query import word_frequency
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


def glove_to_vector_map(filename):
    vector_map = defaultdict(list)
    with open(filename, encoding='latin-1') as file:
        for i, line in enumerate(file):
            parts = line.rstrip().split(' ')

            try:
                ctext = fix_text(parts[0]).replace('\n', '').strip()
                concept = conceptnet_normalizer(ctext)
            except ValueError: #TODO document cause of exception
                continue

            zipf_weight = 1 / (i + 1)
            vec = np.array(
                [float(part) for part in parts[1:]]
            )
            vector_map[concept].append(vec * zipf_weight)
    return vector_map


def load_glove_vectors(filename, labels, filter_beyond_row=250000,
                        end_row=1000000, frequency_cutoff=1e-6):
    vectors = []
    with open(filename, encoding='latin-1') as file:
        for i, line in enumerate(file):
            if i >= end_row:
                break
            parts = line.rstrip().split(' ')
            try:
                ctext = fix_text(parts[0]).replace('\n', '').strip()
                concept = conceptnet_normalizer(ctext)
                if i >= filter_beyond_row and \
                    word_frequency(ctext, 'en') < frequency_cutoff:
                    continue
            except ValueError: #TODO document cause of exception
                continue
            index = labels.add(concept)
            while index >= len(vectors):
                vectors.append(np.zeros(300))
            zipf_weight = 1 / (i + 1)
            vec = np.array([float(part) for part in parts[1:]])
            vectors[index] += vec * zipf_weight
    return vectors


def make_sparse_assoc(filename, labels):
    rows = []
    cols = []
    values = []
    totals = defaultdict(float)
    print("Loading sparse associations")
    with open(filename, encoding='utf-8') as infile:
        for line in infile:
            line = line.rstrip()
            concept1, concept2, value_str = line.split('\t')
            index1 = labels.add(concept1)
            index2 = labels.add(concept2)
            value = float(value_str)
            rows.append(index1)
            cols.append(index2)
            values.append(value)
            rows.append(index2)
            cols.append(index1)
            values.append(value)
            totals[concept1] += value
            totals[concept2] += value

    print("Adding self-loops and negations")
    for concept in labels:
        index1 = labels.index(concept)
        rows.append(index1)
        cols.append(index1)
        values.append(totals[concept] + 10)

        neg = negate_concept(concept)
        if neg in labels:
            index2 = labels.index(neg)
            rows.append(index1)
            cols.append(index2)
            values.append(-0.5)
            rows.append(index2)
            cols.append(index1)
            values.append(-0.5)

    print("Building sparse matrix")
    sparse_csr = sparse.coo_matrix((values, (rows, cols))).tocsr()
    return sparse_csr


def retrofit(dense_file, sparse_file, output_file):
    labels = LabelSet()
    vectors = load_glove_vectors(dense_file, labels)
    sparse_csr = make_sparse_assoc(sparse_file, labels)
    dense = np.zeros((len(labels), 300))
    print("Building dense matrix")
    for i in range(len(vectors)):
        dense[i] = vectors[i]

    print("Retrofitting")
    orig_dense = normalize_rows(dense, offset=1e-9)
    for iter in range(10):
        print("%d/10" % (iter + 1))
        product = sparse_csr.dot(dense)
        # mean = np.mean(product, axis=0)
        # product -= mean

        newdense = normalize_rows(product, offset=1e-9)
        del product

        newdense[:len(vectors)] += orig_dense[:len(vectors)]
        newdense[:len(vectors)] /= 2
        diff = np.mean(np.abs(newdense - dense))
        dense = newdense
        print("   Average diff: %s" % diff)

    assoc = AssocSpace(dense, np.ones(300), labels, assoc=dense)
    assoc.save_dir(output_file)


def main():
    import sys
    retrofit(sys.argv[1], sys.argv[2], sys.argv[3])


if __name__ == '__main__':
    main()
