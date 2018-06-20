import io
import numpy as np
import pandas as pd

from collections import defaultdict
from conceptnet5.uri import get_uri_language
from conceptnet5.vectors.propagate import sharded_propagate, make_adjacency_matrix, propagate
from nose.tools import with_setup, ok_, eq_
from numpy.testing import assert_allclose
from scipy import sparse
from unittest.mock import patch, Mock

N_EMBEDDING_TERMS = 50
EMBEDDING_DIM = 4
N_EXTRA_GRAPH_TERMS = 30
GRAPH_EDGE_PROBA = 0.25
LANGUAGES = ['en', 'fr']
LANGUAGE_PROBA = [0.5, 0.5]
WEIGHTS = [0.5, 1.0, 1.5]
WEIGHT_PROBA = [0.25, 0.5, 0.25]
DATASETS = ['/d/wiktionary/en', '/d/wiktionary/fr']
DATASET_PROBA = [0.8, 0.2]
RELATIONS = ['/r/RelatedTo', '/r/Synonym']
RELATION_PROBA = [0.75, 0.25]

FRAME = None
EDGE_LIST = None
EDGE_SET = None
NEW_ENGLISH_TERMS = None
NEW_NON_ENGLISH_TERMS = None
COMBINED_INDEX = None
ADJACENCY_MATRIX = None
RANK = None

random_gen = np.random.RandomState(101) # fix a random seed


def extract_positional_arg(mock_obj, call_number, position):
    """
    Given a unittest.mock object (which has been used to mock some callable), 
    a call number (less than the number of times the mock object has been 
    called) and a position, return the positional argument at that position 
    for the given call of the object.
    """
    if len(mock_obj.call_args_list) <= call_number:
        return None
    call_args = mock_obj.call_args_list[call_number]
    positional_args = call_args[0]
    if len(positional_args) <= position:
        return None
    return positional_args[position]


def make_term(i_term):
    language = random_gen.choice(LANGUAGES, p=LANGUAGE_PROBA)
    term = '/c/{}/term{}'.format(language, i_term)
    return term


def setup_frame_and_edges():
    global FRAME, EDGE_LIST, EDGE_SET
    global NEW_ENGLISH_TERMS, NEW_NON_ENGLISH_TERMS
    global ADJACENCY_MATRIX, COMBINED_INDEX, RANK

    # Make a frame with synthetic terms and random embedding vectors.
    terms = [make_term(i_term) for i_term in range(N_EMBEDDING_TERMS + N_EXTRA_GRAPH_TERMS)]
    frame_index = pd.Index(terms[:N_EMBEDDING_TERMS])
    frame_data = random_gen.randn(len(frame_index), EMBEDDING_DIM)
    FRAME = pd.DataFrame(data=frame_data, index=frame_index)

    # Construct a random concept graph by making its set of edges (pairs of
    # terms) and vertices (single terms), and create an association edge list
    # for it in the appropriate format for reading by the code under test.
    EDGE_LIST = []
    EDGE_SET = set()
    graph_terms = set()
    for left in terms:
        for right in terms:
            if left == right:
                continue # make no self-edges
            if random_gen.uniform() < GRAPH_EDGE_PROBA:
                weight = random_gen.choice(WEIGHTS, p=WEIGHT_PROBA)
                dataset = random_gen.choice(DATASETS, p=DATASET_PROBA)
                rel = random_gen.choice(RELATIONS, p=RELATION_PROBA)
                EDGE_LIST.append('\t'.join([left, right, str(weight), dataset, rel]))
                EDGE_SET.add((left, right))
                EDGE_SET.add((right, left)) # the graph should be undirected
                graph_terms.add(left)
                graph_terms.add(right)
    EDGE_LIST = '\n'.join(EDGE_LIST)

    # Find the sets of terms in the frame, and of additional terms in the
    # graph not in the frame (keeping in mind that not every term constructed
    # above may have made it into the graph), in English and not.
    frame_terms = set(FRAME.index)
    all_terms = graph_terms | frame_terms
    new_terms = all_terms - frame_terms
    NEW_ENGLISH_TERMS = set(
        term for term in new_terms if get_uri_language(term) == 'en')
    NEW_NON_ENGLISH_TERMS = new_terms - NEW_ENGLISH_TERMS

    # Make an index containing the terms of the frame, followed by the non-
    # English terms of the graph not in the frame, followed by the English ones.
    COMBINED_INDEX = pd.Index(
        list(frame_terms) + \
        list(NEW_NON_ENGLISH_TERMS) + \
        list(NEW_ENGLISH_TERMS)
    )

    # Make the adjacency matrix of the graph.
    values = []
    rows = []
    cols = []
    for left in COMBINED_INDEX:
        for right in COMBINED_INDEX:
            if (left, right) in EDGE_SET:
                values.append(np.int8(1))
                rows.append(COMBINED_INDEX.get_loc(left))
                cols.append(COMBINED_INDEX.get_loc(right))
    ADJACENCY_MATRIX = sparse.coo_matrix(
        (values, (rows, cols)),
        shape=(len(COMBINED_INDEX), len(COMBINED_INDEX)),
        dtype=np.int8
    ).tocsr()

    # Rank the vertices of the graph by their distances from the set of terms
    # from the frame.
    RANK = defaultdict(lambda : len(COMBINED_INDEX))
    for term in FRAME.index:
        RANK[term] = 0
    for stage in range(len(new_terms)):
        for term in new_terms:
            if RANK[term] <= stage:
                continue
            for other_term in COMBINED_INDEX:
                if (term, other_term) in EDGE_SET and RANK[other_term] <= stage:
                    RANK[term] = stage + 1


@with_setup(setup_frame_and_edges)
def test_adjacency_matrix():
    with patch('builtins.open', return_value=io.StringIO(EDGE_LIST)):
        adjacency_matrix, combined_index, n_new_english = make_adjacency_matrix(
            'ignored_filename', FRAME.index)
    
    # The adjacency matrix must be square with one row for each term in the
    # combined index.
    eq_(len(adjacency_matrix.shape), 2)
    eq_(adjacency_matrix.shape[0], len(combined_index))
    eq_(adjacency_matrix.shape[1], len(combined_index))

    # Each entry must be 0 or 1 according to whether the corresponding terms
    # are joined by an edge in the graph.  Note that it is problematic to
    # compare entries directly with the reference ADJACENCY_MATRIX as its
    # rows and columns may be permuted with respect to the computed matrix.
    for i_left in range(len(combined_index)):
        left = combined_index[i_left]
        for i_right in range(len(combined_index)):
            right = combined_index[i_right]
            is_edge = (left, right) in EDGE_SET
            entry = adjacency_matrix[i_left, i_right]
            ok_((entry == 0) or (entry == 1))
            eq_(entry == 1, is_edge)


@with_setup(setup_frame_and_edges)
def test_combined_index():
    with patch('builtins.open', return_value=io.StringIO(EDGE_LIST)):
        adjacency_matrix, combined_index, n_new_english = make_adjacency_matrix(
            'ignored_filename', FRAME.index)

    # The computed combined index must have the same terms as the reference,
    # but possibly in a different order.
    eq_(set(combined_index), set(COMBINED_INDEX))

    # No term should be listed twice in the combined index.
    eq_(len(combined_index), len(set(combined_index)))

    # The terms from the frame must preceed any other terms from the graph.
    n_frame_terms = len(FRAME.index)
    eq_(set(combined_index[:n_frame_terms]), set(FRAME.index))

    # Among the remaining terms, the terms in English must come last, and
    # their number must be reported correctly.
    eq_(n_new_english, len(NEW_ENGLISH_TERMS))
    n_new_non_english = len(NEW_NON_ENGLISH_TERMS)
    eq_(set(combined_index[n_frame_terms:(n_frame_terms + n_new_non_english)]),
        NEW_NON_ENGLISH_TERMS)
    eq_(set(combined_index[(n_frame_terms + n_new_non_english):]),
        NEW_ENGLISH_TERMS)


@with_setup(setup_frame_and_edges)
def test_propagate():
    propagated = propagate(
        COMBINED_INDEX, FRAME, ADJACENCY_MATRIX, len(NEW_ENGLISH_TERMS)
    )

    # The propagated terms should be the terms from the conbined index,
    # starting with the terms of the frame and going up to the last new
    # term from the graph that is not in English.
    eq_(len(propagated), len(FRAME) + len(NEW_NON_ENGLISH_TERMS))
    for i_term in range(len(propagated)):
        eq_(propagated.index[i_term], COMBINED_INDEX[i_term])
    
    # The original embedding should not be altered.
    assert_allclose(propagated.values[:len(FRAME), :], FRAME.values)

    # Terms not from the original embedding should be assigned the 
    # average of the vectors of their neighbors of lesser rank, if all
    # of those neighbors are either from the original embedding or non-
    # English.
    for term in NEW_NON_ENGLISH_TERMS:
        count = 0
        sum = np.zeros((EMBEDDING_DIM,), dtype=np.float32)
        for other_term in COMBINED_INDEX:
            if (
                (term, other_term) in EDGE_SET
                    and RANK[other_term] < RANK[term]
            ):
                if other_term in NEW_ENGLISH_TERMS:
                    break
                count += 1
                sum = np.add(sum, propagated.loc[other_term])
        else:
            assert_allclose(propagated.loc[term], sum/count)


@with_setup(setup_frame_and_edges)
def test_sharded_propagate():
    # Run the sharded propagation code over the test data in 2 shards.
    nshards = 2
    shard_catcher = Mock(return_value=None)
    with patch('builtins.open', return_value=io.StringIO(EDGE_LIST)), \
         patch('conceptnet5.vectors.propagate.make_adjacency_matrix',
               return_value=(ADJACENCY_MATRIX, COMBINED_INDEX, len(NEW_ENGLISH_TERMS))), \
         patch('conceptnet5.vectors.propagate.load_hdf', return_value=FRAME), \
         patch('conceptnet5.vectors.propagate.save_hdf', shard_catcher):
        sharded_propagate(
            'ignored_assoc_file',
            'ignored_embedding_file',
            'shard_filename_root',
            nshards=nshards
        )

    # Run unsharded propagation for comparison.
    propagated = propagate(
        COMBINED_INDEX, FRAME, ADJACENCY_MATRIX, len(NEW_ENGLISH_TERMS)
    )

    # Check that two shard files were written, to the correct filenames.
    shard_arg = 0  # shard is 1st arg to save_hdf
    fname_arg = 1  # filename is 2nd arg to save_hdf.
    eq_(len(shard_catcher.call_args_list), nshards)
    for i_shard in range(nshards):
        filename = extract_positional_arg(shard_catcher, i_shard, fname_arg)
        eq_(filename, 'shard_filename_root.shard{}'.format(i_shard))

    # The shards should agree with the appropriate pieces of the unsharded output.
    for i_shard in range(nshards):
        shard = extract_positional_arg(shard_catcher, i_shard, shard_arg)
        shard_start_dim = i_shard * EMBEDDING_DIM // nshards
        shard_end_dim = shard_start_dim + EMBEDDING_DIM // nshards
        eq_(len(shard.index), len(propagated.index))
        for shard_term, ref_term in zip(shard.index, propagated.index):
            eq_(shard_term, ref_term)
        assert_allclose(shard.values, propagated.values[:, shard_start_dim:shard_end_dim])
