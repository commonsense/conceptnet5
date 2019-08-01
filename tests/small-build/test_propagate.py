import io
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
from numpy.testing import assert_allclose
from scipy import sparse

from conceptnet5.uri import concept_uri, get_uri_language
from conceptnet5.vectors.propagate import (
    make_adjacency_matrix,
    propagate,
    sharded_propagate,
)

# Constant parameters.
N_TRIALS = 20
EMBEDDING_DIM = 4
MAX_N_GRAPH_TERMS = 40
MAX_N_EXTRA_FRAME_TERMS = 5
GRAPH_EDGE_PROBA = 0.4
LANGUAGES = ['en', 'fr']
NON_ENGLISH_LANGUAGES = ['fr', 'zh']
LANGUAGE_PROBA = [0.8, 0.2]
WEIGHTS = [0.5, 1.0, 1.5]
WEIGHT_PROBA = [0.25, 0.5, 0.25]
DATASETS = ['/d/wiktionary/en', '/d/wiktionary/fr']
DATASET_PROBA = [0.8, 0.2]
RELATIONS = ['/r/RelatedTo', '/r/Synonym']
RELATION_PROBA = [0.75, 0.25]

# Test fixture data (to be setup/torn-down later).
FRAME = None
ASSOC_FILE_CONTENTS = None
EDGE_SET = None
NEW_ENGLISH_TERMS = None
NEW_NON_ENGLISH_TERMS = None
COMBINED_INDEX = None
ADJACENCY_MATRIX = None
RANKS = None

# Test data will be generated pseudo-randomly, but with a fixed seed to
# ensure reproducability.
random_gen = np.random.RandomState(101)


def do_setup(setup=None, teardown=None):
    """
    A decorator like nose's with_setup, but can be used to wrap functions other 
    than nose tests.  When a function that has been wrapped by do_setup is 
    called, the setup function supplied (if any) will be called (with no 
    arguments), then the decorated function, then the teardown function (if 
    any, and with no arguments).
    """

    def decorate(func):
        def newfunc(*args, **kwargs):
            if setup is not None:
                setup()
            func(*args, **kwargs)
            if teardown is not None:
                teardown()

        return newfunc

    return decorate


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


_term_count = 0


def _numbers_to_letters(num):
    """
    Write base-10 numbers using the alphabet 'qrstuvwxyz', so that they won't be
    normalized away.
    """
    numstr = str(num)
    for digit in '0123456789':
        letter = chr(ord(digit) - ord('0') + ord('q'))
        numstr = numstr.replace(digit, letter)
    return numstr


def make_term():
    """
    Make and return a string representing a (synthetic) term in a randomly-
    chosen language.
    """
    global _term_count
    language = random_gen.choice(LANGUAGES, p=LANGUAGE_PROBA)
    term_letters = _numbers_to_letters(_term_count)
    term_text = 'term_{}'.format(term_letters)
    term = concept_uri(language, term_text)
    _term_count += 1
    return term


def make_term_list(length):
    """
    Make and return a list of terms, of the requested length, each generated 
    by make_term.
    """
    terms = [make_term() for i_term in range(length)]
    return terms


def make_random_frame(terms):
    """
    Make a frame with the given terms and random embedding vectors.
    """
    frame_index = pd.Index(terms)
    frame_data = random_gen.randn(len(frame_index), EMBEDDING_DIM)
    frame = pd.DataFrame(data=frame_data, index=frame_index)
    return frame


class ConceptNetRandomTestGraph:
    """
    Instances are randomly-generated association graphs suitable for testing 
    propagation code.
    """

    def __init__(self, max_n_terms=MAX_N_GRAPH_TERMS):
        """
        Construct a random concept graph by making its set of edges (pairs of
        terms) and vertices (single terms), and create an association edge list
        for it in the appropriate format for reading by the code under test.  
        Note that the resulting set of vertices/terms may not have the full 
        number of terms requested, as we do not include vertices without any 
        incident edges in the output.
        """
        # Represent the graph as simply as possible, namely with a set of
        # vertices (terms) and a set of edges (pairs of vertices).
        self.vertices = set()
        self.edge_set = set()

        # But we also need a representation of the graph readable as an
        # assoc file to feed to code to be tested.
        self.assoc_file_contents = []

        # We ensure some variability in the connectivity of the generated
        # graphs, by choosing a random number (at least one) of "pieces"
        # (by which we mean unions of connected components), and enforcing
        # that there are no edges between pieces.  (We don't enforce that
        # each piece is connected, as that would be a bother.)  To make
        # realistic test data, we make all but the first piece small.
        n_pieces = random_gen.choice(3) + 1
        piece_sizes = [0] * n_pieces
        piece_sizes[0] = max_n_terms
        for i_piece in range(1, n_pieces):
            piece_sizes[i_piece] = random_gen.choice(max_n_terms // 5)
            piece_sizes[0] -= piece_sizes[i_piece]

        terms = []
        pieces = []
        piece_map = {}
        for i_piece, piece_size in enumerate(piece_sizes):
            piece = make_term_list(piece_size)
            for term in piece:
                piece_map[term] = i_piece
                terms.append(term)
            pieces.append(piece)

        # Create edges, and populate the edge and vertex sets, and the associations.
        for left in terms:
            for right in terms:
                if left <= right:
                    continue  # make no self-edges, consider each pair only once
                if piece_map[left] != piece_map[right]:
                    continue  # make no edges between pieces
                if random_gen.uniform() < GRAPH_EDGE_PROBA:
                    weight = random_gen.choice(WEIGHTS, p=WEIGHT_PROBA)
                    dataset = random_gen.choice(DATASETS, p=DATASET_PROBA)
                    rel = random_gen.choice(RELATIONS, p=RELATION_PROBA)
                    self.assoc_file_contents.append(
                        '\t'.join([left, right, str(weight), dataset, rel])
                    )
                    self.edge_set.add((left, right))
                    self.edge_set.add((right, left))  # make the graph undirected
                    self.vertices.add(
                        left
                    )  # only collect vertices on at least one edge
                    self.vertices.add(right)
        self.assoc_file_contents = '\n'.join(self.assoc_file_contents)

        # Save the pieces (for use in making frames to use with the graph).
        pieces = [[term for term in piece if term in self.vertices] for piece in pieces]
        self.pieces = [piece for piece in pieces if len(piece) > 0]

    def make_frame(self, max_n_extra_terms=MAX_N_EXTRA_FRAME_TERMS):
        """
        Return a frame to use together with this graph in testing.  The 
        frame will have controlled probability of satsifying edge cases 
        concerning its overlap with connected components of the graph.
        """
        n_extra_terms = random_gen.choice(max_n_extra_terms + 1)
        terms = make_term_list(n_extra_terms)
        for i_piece, piece in enumerate(self.pieces):
            if i_piece == 0:  # Take a random subset of the big piece.
                n_terms = random_gen.choice(len(piece))
                new_terms = list(random_gen.choice(piece, size=n_terms, replace=False))
            else:  # Take no, one, or all the elements of any other piece.
                none = []
                one = [random_gen.choice(piece)]
                new_terms = random_gen.choice([none, one, piece])
            terms.extend(new_terms)
        random_gen.shuffle(terms)  # destroy order by pieces
        frame = make_random_frame(terms)
        return frame

    def combined_index_and_new_term_sets(self, frame):
        """
        Find the sets of terms in the frame, and of additional terms in the
        graph not in the frame, but at finite distance in the graph from the 
        terms of the frame, in English and not.  Using these construct a 
        combined index satisfying the constraints required for input to 
        propagation (terms of the frame must come first, then terms from the 
        (vertices of) the graph not in the frame, with the non-English terms 
        not from the frame preceeding the English terms not from the frame).
        
        Returns the combined index, the set of non-English terms from the 
        graph not in the frame, and the set of English terms from the graph 
        not in the frame.
        """
        frame_terms = set(frame.index)

        # Get the ranks of the vertices of the graph with respect to the frame,
        # and use them to eliminate all vertices not a finite distance from the
        # frame.
        ranks = self.rank_vertices(frame)
        graph_terms = set(term for term in self.vertices if ranks[term] != -1)

        all_terms = graph_terms | frame_terms
        new_terms = all_terms - frame_terms
        new_english_terms = set(
            term for term in new_terms if get_uri_language(term) == 'en'
        )
        new_non_english_terms = new_terms - new_english_terms

        combined_index = pd.Index(
            list(frame_terms) + list(new_non_english_terms) + list(new_english_terms)
        )
        return combined_index, new_non_english_terms, new_english_terms

    def adjacency_matrix(self, combined_index):
        """
        Return the adjacency matrix of the graph with respect to the given 
        index.  That is, a (sparse) square matrix with one row and column for 
        each entry in the index, such that any entry is one if and only if the 
        corresponding terms from the index are joined by an edge in the graph.
        """
        values = []
        rows = []
        cols = []
        for left in combined_index:
            for right in combined_index:
                if (left, right) in self.edge_set:
                    values.append(np.int8(1))
                    rows.append(combined_index.get_loc(left))
                    cols.append(combined_index.get_loc(right))

        adjacency_matrix = sparse.coo_matrix(
            (values, (rows, cols)),
            shape=(len(combined_index), len(combined_index)),
            dtype=np.int8,
        ).tocsr()
        return adjacency_matrix

    def rank_vertices(self, frame):
        """
        Rank the vertices of the graph by their distances from the set of terms
        from the frame, and return a dict mapping each vertex to its rank.  
        (Vertices not at a finite distance from the frame will be assigned a 
        rank of -1.)
        """
        # Let ranks default to a value larger than any possible valid rank.
        bigger_than_any_rank = len(self.vertices)
        ranks = {vertex: bigger_than_any_rank for vertex in self.vertices}

        # But terms from the frame have rank 0.
        for term in frame.index:
            ranks[term] = 0

        # If any edge has a rank difference more than one, reduce the rank of
        # the higher-ranked end to make the difference one.  This leaves every
        # vertex assigned a rank greater or equal to its true rank.  Repeat
        # until there are no more such differences; then every vertex assigned
        # rank zero is truly rank zero, every vertex assigned rank one is truly
        # rank one, etc.
        done = False
        while not done:
            done = True
            for left, right in self.edge_set:
                if ranks[left] > ranks[right] + 1:
                    ranks[left] = ranks[right] + 1
                    done = False
                elif ranks[right] > ranks[left] + 1:
                    ranks[right] = ranks[left] + 1
                    done = False

        for vertex, r in ranks.items():
            if r == bigger_than_any_rank:
                ranks[vertex] = -1
        return ranks


# Setup and teardown functions to create/erase a single test data instance.


def setup_frame_and_edges():
    global FRAME, ASSOC_FILE_CONTENTS, EDGE_SET
    graph = ConceptNetRandomTestGraph()
    FRAME = graph.make_frame()
    ASSOC_FILE_CONTENTS = graph.assoc_file_contents
    EDGE_SET = graph.edge_set


def setup_combined_index():
    global FRAME, ASSOC_FILE_CONTENTS
    global COMBINED_INDEX, NEW_ENGLISH_TERMS, NEW_NON_ENGLISH_TERMS
    graph = ConceptNetRandomTestGraph()
    FRAME = graph.make_frame()
    ASSOC_FILE_CONTENTS = graph.assoc_file_contents
    COMBINED_INDEX, NEW_NON_ENGLISH_TERMS, NEW_ENGLISH_TERMS = graph.combined_index_and_new_term_sets(
        FRAME
    )


def setup_adjacency_matrix():
    global FRAME, ASSOC_FILE_CONTENTS
    global COMBINED_INDEX, NEW_ENGLISH_TERMS, NEW_NON_ENGLISH_TERMS
    global ADJACENCY_MATRIX
    graph = ConceptNetRandomTestGraph()
    FRAME = graph.make_frame()
    ASSOC_FILE_CONTENTS = graph.assoc_file_contents
    COMBINED_INDEX, NEW_NON_ENGLISH_TERMS, NEW_ENGLISH_TERMS = graph.combined_index_and_new_term_sets(
        FRAME
    )
    ADJACENCY_MATRIX = graph.adjacency_matrix(COMBINED_INDEX)


def setup_ranks():
    global FRAME, ASSOC_FILE_CONTENTS, EDGE_SET
    global COMBINED_INDEX, NEW_ENGLISH_TERMS, NEW_NON_ENGLISH_TERMS
    global ADJACENCY_MATRIX, RANKS
    graph = ConceptNetRandomTestGraph()
    FRAME = graph.make_frame()
    ASSOC_FILE_CONTENTS = graph.assoc_file_contents
    EDGE_SET = graph.edge_set
    COMBINED_INDEX, NEW_NON_ENGLISH_TERMS, NEW_ENGLISH_TERMS = graph.combined_index_and_new_term_sets(
        FRAME
    )
    ADJACENCY_MATRIX = graph.adjacency_matrix(COMBINED_INDEX)
    RANKS = graph.rank_vertices(FRAME)


def teardown_all():
    global FRAME, ASSOC_FILE_CONTENTS, EDGE_SET
    global COMBINED_INDEX, NEW_ENGLISH_TERMS, NEW_NON_ENGLISH_TERMS
    global ADJACENCY_MATRIX, RANKS
    FRAME = None
    ASSOC_FILE_CONTENTS = None
    EDGE_SET = None
    COMBINED_INDEX = None
    NEW_ENGLISH_TERMS = None
    NEW_NON_ENGLISH_TERMS = None
    ADJACENCY_MATRIX = None
    RANKS = None


@do_setup(setup_frame_and_edges, teardown_all)
def single_test_adjacency_matrix():
    # Call the code under test, but feed it an association list from the test
    # fixture rather than from a file.
    with patch('builtins.open', return_value=io.StringIO(ASSOC_FILE_CONTENTS)):
        adjacency_matrix, combined_index, n_new_english = make_adjacency_matrix(
            'ignored_filename', FRAME.index
        )

    # The adjacency matrix must be square with one row for each term in the
    # combined index.
    assert len(adjacency_matrix.shape) == 2, 'Adjacency matrix must be 2D.'
    assert adjacency_matrix.shape[0] == len(
        combined_index
    ), 'Adjacency matrix must have one row for each term of the combined index.'
    assert adjacency_matrix.shape[1] == len(
        combined_index
    ), 'Adjacency matrix must have one column for each term of the combined index.'

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
            assert (entry == 0) or (
                entry == 1
            ), 'Invalid entry {} in adjacency matrix at row {} ({}) and column {} ({}).'.format(
                entry, i_left, left, i_right, right
            )
            if (left, right) in EDGE_SET:
                assert (
                    entry == 1
                ), 'Edge between {} (row {}) and {} (column {}) missing in adjacency matrix.'.format(
                    left, i_left, right, i_right
                )
            else:
                assert (
                    entry == 0
                ), 'Adjacency matrix incorrectly indicates an edge between {} (row {}) and {} (column {}).'.format(
                    left, i_left, right, i_right
                )


@do_setup(setup_combined_index, teardown_all)
def single_test_combined_index():
    # Call the code under test, but feed it an association list from the test
    # fixture rather than from a file.
    with patch('builtins.open', return_value=io.StringIO(ASSOC_FILE_CONTENTS)):
        adjacency_matrix, combined_index, n_new_english = make_adjacency_matrix(
            'ignored_filename', FRAME.index
        )

    # The computed combined index must have the same terms as the reference,
    # but possibly in a different order.
    assert set(combined_index) == set(
        COMBINED_INDEX
    ), 'Computed combined index has incorrect terms.'

    # No term should be listed twice in the combined index.
    assert len(combined_index) == len(
        set(combined_index)
    ), 'Computed combined index has repeated terms.'

    # The terms from the frame must preceed any other terms from the graph.
    n_frame_terms = len(FRAME.index)
    assert set(combined_index[:n_frame_terms]) == set(
        FRAME.index
    ), 'Computed combined index does not start with the original terms from the embedding.'

    # Among the remaining terms, the terms in English must come last, and
    # their number must be reported correctly.
    assert n_new_english == len(
        NEW_ENGLISH_TERMS
    ), 'Incorrect number {} (should be {}) of new terms from the association graph in English.'.format(
        n_new_english, len(NEW_ENGLISH_TERMS)
    )
    n_new_non_english = len(NEW_NON_ENGLISH_TERMS)
    assert (
        set(combined_index[n_frame_terms : (n_frame_terms + n_new_non_english)])
        == NEW_NON_ENGLISH_TERMS
    ), 'Incorrect list of new terms from the association graph not in English.'
    assert (
        set(combined_index[(n_frame_terms + n_new_non_english) :]) == NEW_ENGLISH_TERMS
    ), 'Incorrect list of new terms from the association graph in English.'


@do_setup(setup_ranks, teardown_all)
def single_test_propagate():
    # Call the code under test.
    propagated = propagate(
        COMBINED_INDEX, FRAME, ADJACENCY_MATRIX, len(NEW_ENGLISH_TERMS)
    )

    # The propagated terms should be the terms from the conbined index,
    # starting with the terms of the frame and going up to the last new
    # term from the graph that is not in English.
    assert len(propagated) == len(FRAME) + len(
        NEW_NON_ENGLISH_TERMS
    ), 'Incorrect number {} (should be {}) of propagated terms.'.format(
        len(propagated), len(FRAME) + len(NEW_NON_ENGLISH_TERMS)
    )
    for i_term in range(len(propagated)):
        assert (
            propagated.index[i_term] == COMBINED_INDEX[i_term]
        ), 'Propagated output terms do not agree with the input terms.'

    # The original embedding should not be altered.
    assert_allclose(
        propagated.values[: len(FRAME), :],
        FRAME.values,
        err_msg='Propagation changed an input embedding vector.',
    )

    # Terms not from the original embedding should be assigned the
    # average of the vectors of their neighbors of lesser rank, if all
    # of those neighbors are either from the original embedding or non-
    # English.
    for term in NEW_NON_ENGLISH_TERMS:
        count = 0
        sum = np.zeros((EMBEDDING_DIM,), dtype=np.float32)
        for other_term in COMBINED_INDEX:
            if (term, other_term) in EDGE_SET and RANKS[other_term] < RANKS[term]:
                if other_term in NEW_ENGLISH_TERMS:
                    break
                count += 1
                sum = np.add(sum, propagated.loc[other_term])
        else:
            assert_allclose(
                propagated.loc[term],
                sum / count,
                err_msg='Incorrect propagated vector for term {}'.format(term),
            )


@do_setup(setup_adjacency_matrix, teardown_all)
def single_test_sharded_propagate():
    # Run the sharded propagation code over the test data in 2 shards.
    # We patch several functions with mock objects:  sharded_propagate reads
    # an assoc edge file, so we patch builtins.open to give sharded_propagate
    # the test data graph as that input.  It reads an embedding (a dataframe)
    # as well, and we patch load_hdf to give it the test data frame.  It writes
    # a shard file for each shard, so we patch save_hdf with a mock object
    # that we will later query to retrieve the output shards for testing.
    # Finally we patch make_adjacency_matrix with a mock object that returns
    # the known good test data for the adjacency matrix, combined index, and
    # number of new terms in English, to make this test independent of any
    # failures of that function.
    nshards = 2
    shard_collector = Mock(return_value=None)  # save_hdf returns None
    with patch('builtins.open', return_value=io.StringIO(ASSOC_FILE_CONTENTS)), patch(
        'conceptnet5.vectors.propagate.make_adjacency_matrix',
        return_value=(ADJACENCY_MATRIX, COMBINED_INDEX, len(NEW_ENGLISH_TERMS)),
    ), patch('conceptnet5.vectors.propagate.load_hdf', return_value=FRAME), patch(
        'conceptnet5.vectors.propagate.save_hdf', shard_collector
    ):
        sharded_propagate(
            'ignored_assoc_file',
            'ignored_embedding_file',
            'shard_filename_root',
            nshards=nshards,
        )

    # Run unsharded propagation for comparison.
    propagated = propagate(
        COMBINED_INDEX, FRAME, ADJACENCY_MATRIX, len(NEW_ENGLISH_TERMS)
    )

    # Check that two shard files were written, to the correct filenames.
    shard_arg = 0  # shard is 1st arg to save_hdf
    fname_arg = 1  # filename is 2nd arg to save_hdf.
    assert (
        len(shard_collector.call_args_list) == nshards
    ), 'Incorrect number {} (should be {}) of shards written.'.format(
        len(shard_collector.call_args_list), nshards
    )
    for i_shard in range(nshards):
        # Get the positional argument in the filename position of the (i_shard)-th
        # call to the shard_collector Mock object (which mocks save_hdf).
        filename = extract_positional_arg(shard_collector, i_shard, fname_arg)
        assert filename == 'shard_filename_root.shard{}'.format(
            i_shard
        ), 'Shard {} written to incorrect file name {}.'.format(i_shard, filename)

    # The shards should agree with the appropriate pieces of the unsharded output.
    for i_shard in range(nshards):
        # Get the positional argument in the shard dataframe position of the
        # (i-shard)-th call to the shard_collector Mock object (which mocks
        # save_hdf).
        shard = extract_positional_arg(shard_collector, i_shard, shard_arg)
        shard_start_dim = i_shard * EMBEDDING_DIM // nshards
        shard_end_dim = shard_start_dim + EMBEDDING_DIM // nshards
        assert len(shard.index) == len(
            propagated.index
        ), 'Shard {} has incorrect length {} (should be {}).'.format(
            i_shard, len(shard.index), len(propagated.index)
        )
        for shard_term, ref_term in zip(shard.index, propagated.index):
            assert (
                shard_term == ref_term
            ), 'Shard {} has term {} where reference has {}.'.format(
                i_shard, shard_term, ref_term
            )
        assert_allclose(
            shard.values,
            propagated.values[:, shard_start_dim:shard_end_dim],
            err_msg='Shard {} has incorrect propagated vectors.'.format(i_shard),
        )


# The test functions generate multiple instances of test data and apply
# lower-level individual tests to each.


def test_adjacency_matrix():
    for i_test in range(N_TRIALS):
        single_test_adjacency_matrix()


def test_combined_index():
    for i_test in range(N_TRIALS):
        single_test_combined_index()


def test_propagate():
    # It is useful to test propagation on graphs with no English terms,
    # where every term's propagated output vector is computable from its
    # output neighbors (and the ranking of the graph).  (By comparison,
    # if there are new English terms their propagated values do not appear
    # in the propagation output and so their neighbors' values cannot
    # necessarily be computed just from the propagation output.)
    global LANGUAGES
    for i_test in range(N_TRIALS):
        single_test_propagate()
    saved_languages = LANGUAGES
    LANGUAGES = NON_ENGLISH_LANGUAGES
    for i_test in range(N_TRIALS):
        single_test_propagate()
    LANGUAGES = saved_languages


def test_sharded_propagate():
    for i_test in range(N_TRIALS):
        single_test_sharded_propagate()
