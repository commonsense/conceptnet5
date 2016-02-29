import pandas as pd
import numpy as np
from collections import defaultdict


# A mapping of the ConceptNet relations we intend to use, and the
# possibly more general relations that we'll map them to, as well as
# the direction in which they should map onto this relation.
#
# A 'forward' mapping means that when the relation maps A to B, the
# generalized relation does as well.
#
# A 'backward' mapping means that when the relation maps A to B, the
# generalized relation maps B to A. This is used, for example, to
# generalize HasA into PartOf.
#
# A 'symmetric' mapping means that the generalized relation maps both
# A to B and B to A, because the relation should be symmetrical.
#
# An 'identity' mapping indicates a relation that, once applied to
# vectors, should map A to A. We skip learning a matrix transformation
# for this kind of relation, because we believe the matrix should be
# the identity matrix.

GENERALIZED_RELATIONS = {
    '/r/RelatedTo': ('/r/RelatedTo', RelType.identity),
    '/r/TranslationOf': ('/r/RelatedTo', RelType.identity),
    '/r/Synonym': ('/r/RelatedTo', RelType.identity),
    '/r/SimilarTo': ('/r/RelatedTo', RelType.identity),

    '/r/Antonym': ('/r/Antonym', RelType.symmetric),

    '/r/PartOf': ('/r/PartOf', RelType.forward),
    '/r/HasA': ('/r/PartOf', RelType.backward),
    '/r/MadeOf': ('/r/PartOf', RelType.backward),

    '/r/HasSubevent': ('/r/HasSubevent', RelType.forward),
    '/r/HasFirstSubevent': ('/r/HasSubevent', RelType.forward),
    '/r/HasLastSubevent': ('/r/HasSubevent', RelType.forward),
    '/r/HasPrerequisite': ('/r/HasSubevent', RelType.forward),
    '/r/IsA': ('/r/IsA', RelType.forward),
    '/r/AtLocation': ('/r/AtLocation', RelType.forward),
    '/r/UsedFor': ('/r/UsedFor', RelType.forward),
    '/r/HasProperty': ('/r/HasProperty', RelType.forward),
    '/r/Causes': ('/r/Causes', RelType.forward),
    '/r/CausesDesire': ('/r/Causes', RelType.forward),
}


def infer_orthogonal_mapping(A, B):
    """
    Let A and B be matrices of dimensions N by k. This function infers
    the best fitting k-by-k matrix that transforms corresponding rows of
    B to rows of A, and whose transpose transforms corresponding rows of
    A to rows of B.
    """
    aU, aΣ, aVt = np.linalg.svd(A, full_matrices=False)
    bU, bΣ, bVt = np.linalg.svd(B, full_matrices=False)

    # In Python 3.5+, the following operation could be written with clearer
    # parentheses as:
    #
    #   aVt.T @ ((aU.T @ bU) @ bVt)
    #
    # aU.T @ bU yields a k-by-k matrix mapping principal components of A
    # to principal components of B. aVt and bVt are the matrices that convert
    # between actual rows of A and B and principal components, so multiplying
    # by these on the outside turns the result into a mapping from rows of A
    # to rows of B.
    return aVt.T.dot((aU.T.dot(bU)).dot(bVt))


def build_separate_relations(labels, filename, relation_map, verbose=True):
    """
    Build separate sparse matrices for each relation.
    """
    dataset_totals = defaultdict(float)
    dataset_counts = defaultdict(int)
    matrix_builders = defaultdict(SparseMatrixBuilder)

    with open(filename, encoding='utf-8') as infile:
        for line in infile:
            concept1, concept2, value_str, dataset, relation = line.strip().split('\t')
            value = float(value_str)
            dataset_label = coarse_dataset(dataset)
            dataset_totals[dataset_label] += value
            dataset_counts[dataset_label] += 1

    with open(filename, encoding='utf-8') as infile:
        rel_matrices = {}
        for line in infile:
            concept1, concept2, value_str, dataset, relation = line.strip().split('\t')
            if relation in relation_map:
                rel_target, rel_type = relation_map[relation]
                index1 = labels.add(standardize(trim_negation(concept1)))
                index2 = labels.add(standardize(trim_negation(concept2)))
                dataset_label = coarse_dataset(dataset)
                value = float(value_str) / (dataset_totals[dataset_label] / dataset_counts[dataset_label])

                if rel_type == RelType.forward or rel_type == RelType.symmetric:
                    matrix_builders[rel_target][index1, index2] = value
                    if rel_type == RelType.forward:
                        matrix_builders[rel_target + '/back'][index2, index1] = value
                if rel_type == RelType.backward or rel_type == RelType.symmetric:
                    matrix_builders[rel_target][index2, index1] = value
                    if rel_type == RelType.backward:
                        matrix_builders[rel_target + '/back'][index1, index2] = value

    return {label: mat.tocsr(shape=(len(labels), len(labels)))
            for (label, mat) in matrix_builders.items()}


class RelType(Enum):
    identity = 0
    forward = 1
    backward = 2
    symmetric = 3


def build_relation_operators_from_conceptnet(frame, filename):
    """
    This function produces a set of operators representing common relations
    in ConceptNet as matrices mapping one kind of vector to another. The return
    value is a 3-axis Panel whose slices are labeled by relations. Each slice
    is a k-by-k operator that transforms k-dimensional vectors according to
    that relation.

    `frame` is a DataFrame mapping ConceptNet terms to vectors, and
    `filename` is a file of weighted ConceptNet assertions as tab-separated
    values.
    """
    relation_gen = generalize_conceptnet_assertions(filename, GENERALIZED_RELATIONS)
    return build_relation_operators(frame, relation_gen)


def generalize_conceptnet_assertions(filename, relations):
    with open(str(filename), encoding='utf-8') as infile:
        for line in infile:
            term1, term2, value_str, dataset, relation = line.strip().split('\t')
            value = float(value_str)
            if relation in relations:
                generalized_rel, direction = relations[relation]
                if direction == RelType.forward or direction == RelType.symmetric:
                    yield term1, term2, relation, value
                if direction == RelType.backward or direction == RelType.symmetric:
                    yield term2, term1, relation, value


def build_relation_operators(frame, relation_gen):
    a_vectors = defaultdict(list)
    b_vectors = defaultdict(list)
    for term1, term2, relation, value in relation_gen:
        if term1 in frame.index and term2 in frame.index:
            a_vectors[relation].append(frame.loc[term1].values * value)
            b_vectors[relation].append(frame.loc[term2].values * value)

    rels = sorted(a_vectors)
    operators = []
    for rel in rels:
        print(rel)
        a_mat = np.stack(a_vectors)
        b_mat = np.stack(b_vectors)
        operators.append(infer_orthogonal_mapping(a_mat, b_mat))

    array3d = np.stack(operators)
    return pd.Panel(data=array3d, items=rels)
    
