from scipy import sparse
import pandas as pd
from conceptnet5.uri import uri_prefixes, uri_prefix
from conceptnet5.relations import SYMMETRIC_RELATIONS
from conceptnet5.languages import CORE_LANGUAGES
from ordered_set import OrderedSet
from collections import defaultdict
from ..vectors import replace_numbers


class SparseMatrixBuilder:
    """
    SparseMatrixBuilder is a utility class that helps build a matrix of
    unknown shape.
    """
    def __init__(self):
        self.row_index = []
        self.col_index = []
        self.values = []

    def __setitem__(self, key, val):
        row, col = key
        self.row_index.append(row)
        self.col_index.append(col)
        self.values.append(val)

    def tocsr(self, shape, dtype=float):
        return sparse.coo_matrix((self.values, (self.row_index, self.col_index)),
                                 shape=shape, dtype=dtype).tocsr()


def build_from_conceptnet_table(filename, orig_index=(), self_loops=True):
    """
    Read a file of tab-separated association data from ConceptNet, such as
    `data/assoc/reduced.csv`. Return a SciPy sparse matrix of the associations,
    and a pandas Index of labels.

    If you specify `orig_index`, then the index of labels will be pre-populated
    with existing labels, and any new labels will get index numbers that are
    higher than the index numbers the existing labels use. This is important
    for producing a sparse matrix that can be used for retrofitting onto an
    existing dense labeled matrix (see retrofit.py).
    """
    mat = SparseMatrixBuilder()

    labels = OrderedSet(orig_index)

    totals = defaultdict(float)
    with open(str(filename), encoding='utf-8') as infile:
        for line in infile:
            concept1, concept2, value_str, dataset, relation = line.strip().split('\t')

            index1 = labels.add(replace_numbers(concept1))
            index2 = labels.add(replace_numbers(concept2))
            value = float(value_str)
            mat[index1, index2] = value
            mat[index2, index1] = value
            totals[index1] += value
            totals[index2] += value

    # Link nodes to their more general versions
    for label in labels:
        prefixes = list(uri_prefixes(label, 3))
        if len(prefixes) >= 2:
            parent_uri = prefixes[-2]
            if parent_uri in labels:
                index1 = labels.index(label)
                index2 = labels.index(parent_uri)
                mat[index1, index2] = 1
                mat[index2, index1] = 1
                totals[index1] += 1
                totals[index2] += 1

    # add self-loops on the diagonal with equal weight to the rest of the row
    if self_loops:
        for key, value in totals.items():
            mat[key, key] = value

    shape = (len(labels), len(labels))
    index = pd.Index(labels)
    return mat.tocsr(shape), index


def get_language(uri):
    return uri.split('/')[2]


def build_features_from_conceptnet_table(filename):
    mat = SparseMatrixBuilder()

    concept_labels = OrderedSet()
    feature_labels = OrderedSet()

    with open(str(filename), encoding='utf-8') as infile:
        for line in infile:
            concept1, concept2, value_str, dataset, relation = line.strip().split('\t')
            concept1 = replace_numbers(concept1)
            concept2 = replace_numbers(concept2)
            value = float(value_str)
            if relation in SYMMETRIC_RELATIONS:
                feature_pairs = []
                if get_language(concept1) in CORE_LANGUAGES:
                    feature_pairs.append(
                        ('{} {} ~'.format(uri_prefix(concept1), relation), concept2)
                    )
                if get_language(concept2) in CORE_LANGUAGES:
                    feature_pairs.append(
                        ('{} {} ~'.format(uri_prefix(concept2), relation), concept1)
                    )
            else:
                if get_language(concept1) in CORE_LANGUAGES:
                    feature_pairs.append(
                        ('{} {} -'.format(uri_prefix(concept1), relation), concept2)
                    )
                if get_language(concept2) in CORE_LANGUAGES:
                    feature_pairs.append(
                        ('- {} {}'.format(uri_prefix(concept2), relation), concept1)
                    )

            feature_counts = defaultdict(int)
            for feature, concept in feature_pairs:
                feature_counts[feature] += 1

            for feature, concept in feature_pairs:
                prefixes = list(uri_prefixes(concept, 3))
                if feature_counts[feature] > 1:
                    for prefix in prefixes:
                        concept_index = concept_labels.add(prefix)
                        feature_index = feature_labels.add(feature)
                        mat[concept_index, feature_index] = value

    # Link nodes to their more general versions
    for concept in concept_labels:
        prefixes = list(uri_prefixes(concept, 3))
        for prefix in prefixes:
            auto_features = [
                '{} {} ~'.format(prefix, 'SimilarTo'),
                '{} {} ~'.format(prefix, 'RelatedTo'),
                '{} {} -'.format(prefix, 'FormOf'),
                '- {} {}'.format(prefix, 'FormOf'),
            ]
            for feature in auto_features:
                concept_index = concept_labels.add(prefix)
                feature_index = feature_labels.add(feature)
                mat[concept_index, feature_index] = value

    shape = (len(concept_labels), len(feature_labels))
    c_index = pd.Index(concept_labels)
    f_index = pd.Index(feature_labels)
    return mat.tocsr(shape), c_index, f_index
