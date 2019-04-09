"""
Implements 'propagation', whereby terms from the full ConceptNet graph are
assigned vectors from the embeddings produced by retrofitting against the
reduced graph.
"""

import numpy as np
import pandas as pd
from scipy.sparse import diags

from conceptnet5.builders.reduce_assoc import ConceptNetAssociationGraph
from conceptnet5.uri import get_uri_language

from .formats import load_hdf, save_hdf
from .sparse_matrix_builder import SparseMatrixBuilder


class ConceptNetAssociationGraphForPropagation(ConceptNetAssociationGraph):
    """
    Subclass of ConceptNetAssociationGraph specialized for use in making
    the full graph of a set of associations as required for propagation.
    """

    def __init__(self):
        super().__init__()
        self.edges = set()

    def add_edge(self, left, right, value, dataset, relation):
        """
        In addition to the superclass's handling of a new edge,
        saves the edges as a set of (left, right) pairs.
        """
        super().add_edge(left, right, value, dataset, relation)
        self.edges.add((left, right))
        self.edges.add((right, left))  # save undirected edges


def sharded_propagate(
    assoc_filename, embedding_filename, output_filename, nshards=6, iterations=20
):
    """
    A wrapper around propagate which reduces memory requirements by
    splitting the embedding into shards (along the dimensions of the
    embedding feature space).
    """
    # frame_box is basically a reference to a single large DataFrame. The
    # DataFrame will at times be present or absent. When it's present, the list
    # contains one item, which is the DataFrame. When it's absent, the list
    # is empty.
    frame_box = [load_hdf(embedding_filename)]
    adjacency_matrix, combined_index, n_new_english = make_adjacency_matrix(
        assoc_filename, frame_box[0].index
    )
    shard_width = frame_box[0].shape[1] // nshards

    for i in range(nshards):
        temp_filename = output_filename + '.shard%d' % i
        shard_from = shard_width * i
        shard_to = shard_from + shard_width
        if len(frame_box) == 0:
            frame_box.append(load_hdf(embedding_filename))
        embedding_shard = pd.DataFrame(frame_box[0].iloc[:, shard_from:shard_to])

        # Delete full_dense_frame while running retrofitting, because it takes
        # up a lot of memory and we can reload it from disk later.
        frame_box.clear()

        propagated = propagate(
            combined_index,
            embedding_shard,
            adjacency_matrix,
            n_new_english,
            iterations=iterations,
        )
        save_hdf(propagated, temp_filename)
        del propagated


def make_adjacency_matrix(assoc_filename, embedding_vocab):
    """
    Build a sparse adjacency matrix for the ConceptNet graph presented
    in the given assoc file, including all terms from the given embedding
    vocabulary and removing all terms from connected components of the graph
    that do not overlap that vocabulary.

    Also builds an index giving all terms from the resulting joined
    graph+embedding vocabulary in the order corresponding to the rows and
    columns of the matrix.  Note that it is guaranteed that the terms from
    the embedding vocabulary will preceed the remaining terms in that index,
    and that among the remaining terms the terms in English will follow all
    the others.

    Returns the matrix and index, and the number of new English terms.
    """
    # First eliminate all connected components of the graph that don't
    # overlap the vocabulary of the embedding; we can't do anything with
    # those terms.

    graph = ConceptNetAssociationGraphForPropagation.from_csv(
        assoc_filename, reject_negative_relations=False
    )
    component_labels = graph.find_components()

    # Get the labels of components that overlap the embedding vocabulary.
    good_component_labels = set(
        label for term, label in component_labels.items() if term in embedding_vocab
    )

    # Now get the concepts in those components.
    good_concepts = set(
        term
        for term, label in component_labels.items()
        if label in good_component_labels
    )

    del component_labels, good_component_labels

    # Put terms from the embedding first, then terms from the good part
    # of the graph neither from the embedding nor in English, then terms
    # from the good part of the graph in English but not from the embedding.
    #
    # (In the corner case where either of these addtional sets of terms is
    # empty, construction of a pandas index will fail using generator rather
    # than list comprehensions.)
    new_vocab = good_concepts - set(embedding_vocab)
    good_concepts = embedding_vocab.append(
        pd.Index([term for term in new_vocab if get_uri_language(term) != 'en'])
    )
    n_good_concepts_not_new_en = len(good_concepts)
    good_concepts = good_concepts.append(
        pd.Index([term for term in new_vocab if get_uri_language(term) == 'en'])
    )
    del new_vocab
    n_new_english = len(good_concepts) - n_good_concepts_not_new_en

    good_concepts_map = {term: i for i, term in enumerate(good_concepts)}

    # Convert the good part of the graph to an adjacency matrix representation.

    # Note: the edges added differ slightly from the way it is done in (e.g.)
    # build_from_conceptnet_table (in sparse_matrix_builder.py), in that we
    # do not add edges linking specific senses of terms to their more general
    # forms (as defined by uri_prefixes).  Currently no such specific senses
    # show up in the input to retrofitting (i.e. the output of
    # build_from_conceptnet_table), so it doesn't matter, but in the future
    # we may want to add such edges here as well.

    builder = SparseMatrixBuilder()
    for v, w in graph.edges:
        try:
            index0 = good_concepts_map[v]
            index1 = good_concepts_map[w]
            builder[index0, index1] = 1
        except KeyError:
            pass  # one of v, w wasn't good
    del graph

    adjacency_matrix = builder.tocsr(
        shape=(len(good_concepts), len(good_concepts)), dtype=np.int8
    )

    return adjacency_matrix, good_concepts, n_new_english


def propagate(
    combined_index, embedding, adjacency_matrix, n_new_english, iterations=20
):
    """
    For as many non-English terms as possible in the ConceptNet graph whose
    edges are presented in the given adjacency matrix (with corresponding term
    labels in the given index), find a vector in the target space of the vector
    embedding presented in the given embedding file.
    """

    # Propagate the vectors from the embeddings to the remaining
    # terms, following the edges of the graph.

    embedding_dimension = embedding.values.shape[1]
    new_vocab_size = len(combined_index) - embedding.values.shape[0]
    vectors = np.vstack(
        [
            embedding.values,
            np.zeros(
                (new_vocab_size, embedding_dimension), dtype=embedding.values.dtype
            ),
        ]
    )

    for iteration in range(iterations):
        zero_indicators = np.abs(vectors).sum(1) == 0
        if not np.any(zero_indicators):
            break
        # Find terms with zero vectors having neighbors with nonzero vectors.
        nonzero_indicators = np.logical_not(zero_indicators)
        fringe = adjacency_matrix.dot(nonzero_indicators.astype(np.int8)) != 0
        fringe = np.logical_and(fringe, zero_indicators)
        # Update each as the average of its nonzero neighbors
        adjacent_nonzeros = adjacency_matrix[fringe, :].dot(
            diags([nonzero_indicators.astype(np.int8)], [0], format='csc')
        )
        n_adjacent_nonzeros = adjacent_nonzeros.sum(axis=1).A[:, 0]
        weights = 1.0 / n_adjacent_nonzeros
        vectors[fringe, :] = adjacency_matrix[fringe, :].dot(vectors)
        vectors[fringe, :] = diags([weights], [0], format='csr').dot(vectors[fringe, :])

    n_old_plus_new_non_en = len(combined_index) - n_new_english
    result = pd.DataFrame(
        index=combined_index[0:n_old_plus_new_non_en],
        data=vectors[0:n_old_plus_new_non_en, :],
    )
    return result
