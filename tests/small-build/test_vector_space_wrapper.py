import os

import pandas as pd
from nose.tools import ok_, with_setup, eq_, assert_raises

from conceptnet5.uri import is_term
from conceptnet5.vectors.query import VectorSpaceWrapper

DATA = os.environ.get("CONCEPTNET_BUILD_DATA", "testdata")
TEST_FRAME = None


def setup_simple_frame():
    data = [[4, 4, 4],
            [1, 1, 1],
            [1, 2, 10],
            [3, 3, 4],
            [2, 3, 4],
            [2, 3, 5],
            [7, 2, 7],
            [3, 8, 2]]

    index = ['island', 'Island', 'cat', 'figure', 'figure skating', 'figure skater', 'thing', '17']
    global TEST_FRAME
    TEST_FRAME = pd.DataFrame(data=data, index=index)


def setup_multi_ling_frame():
    data = [[8, 10, 3],
            [4, 5, 6],
            [4, 4, 5],
            [10, 6, 12],
            [10, 7, 11],
            [20, 20, 7]]
    index = ['/c/pl/kombinacja',
             '/c/en/ski_jumping',
             '/c/en/nordic_combined',
             '/c/en/present',
             '/c/en/gift',
             '/c/en/quiz']
    global TEST_FRAME
    TEST_FRAME = pd.DataFrame(data=data, index=index)


@with_setup(setup_simple_frame)
def test_load():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    ok_(vectors.frame is not None)
    ok_(vectors.small_frame is not None)
    ok_(all(label.startswith('/c/en/') for label in vectors.frame.index))
    ok_(vectors.frame.index.is_monotonic_increasing)
    ok_(vectors.small_frame.shape[1] <= 100)
    ok_(vectors._trie is not None)


@with_setup(setup_simple_frame)
def test_expand_terms():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    # Only expand if


@with_setup(setup_simple_frame)
def test_englishify():
    term = '/c/pl/harry_potter'
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    ok_(vectors._englishify(term), '/c/en/harry_potter')


@with_setup(setup_simple_frame)
def test_match_prefix():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    term = '/c/en/figure_skate'
    expected_prefix_matches = [('/c/en/figure', 0.003),
                ('/c/en/figure skater', 0.003),
                ('/c/en/figure skating', 0.003)]
    prefix_matches = vectors._match_prefix(term=term, prefix_weight=0.01)
    ok_(expected_prefix_matches, prefix_matches)


@with_setup(setup_multi_ling_frame)
def test_lookup_neighbors():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    term = '/c/pl/skoki_narciarskie'
    neighbors = vectors._find_neighbors(term=term, limit_per_term=10,
                                        weight=1.0)
    expected_neighbors = [('/c/en/ski_jumping', 0.02),
                          ('http://pl.dbpedia.org/resource/Skoki_narciarskie', 0.01),
                          ('/c/en/ski_jumping', 0.01),
                          ('/c/en/ski_jumping', 0.005)]
    ok_(expected_neighbors, neighbors)


@with_setup(setup_simple_frame)
def test_vector_space_wrapper():
    """
    Check if VectorSpaceWrapper's index is sorted and its elements are concepts.
    """
    wrap = VectorSpaceWrapper(frame=TEST_FRAME)
    wrap.load()
    ok_(all(is_term(label) for label in wrap.frame.index))
    ok_(wrap.frame.index.is_monotonic_increasing)

    # test there are no transformations to raw terms other than adding the english tag
    ok_('/c/en/figure skater' in wrap.frame.index)  # no underscore
    ok_('/c/en/Island' in wrap.frame.index)  # no case folding

    # test _index_prefix_range
    ok_(wrap._index_prefix_range('/c/en/figure') == (3, 6))
    ok_(wrap._index_prefix_range('/c/en/skating') == (0, 0))

    # test_similar_terms
    ok_('/c/en/figure skating' in wrap.similar_terms('/c/en/figure skating', limit=3).index)
    ok_('/c/en/figure skater' in wrap.similar_terms('/c/en/figure skating', limit=3).index)
    ok_('/c/en/figure' in wrap.similar_terms('/c/en/figure skating', limit=3).index)


@with_setup(setup_multi_ling_frame)
def test_vector_space_wrapper_filter():
    wrap = VectorSpaceWrapper(frame=TEST_FRAME)
    wrap.load()
    ok_('/c/pl/kombinacja' in wrap.similar_terms('/c/en/nordic_combined', filter='/c/pl',
                                                 limit=1).index)

    ok_('/c/en/present' in wrap.similar_terms('/c/en/gift', filter='/c/en/present', limit=1).index)


@with_setup(setup_multi_ling_frame)
def test_missing_language():
    wrap = VectorSpaceWrapper(frame=TEST_FRAME)
    wrap.load()

    # The frame contains no Esperanto, of course, so the out-of-vocabulary
    # mechanism will fail. We should simply get no results, not crash.
    similarity = wrap.similar_terms('/c/eo/ekzemplo')
    eq_(len(similarity), 0)


@with_setup(setup_multi_ling_frame)
def test_cache_with_oov():
    wrap = VectorSpaceWrapper(frame=TEST_FRAME)
    wrap.load()
    # check the vector of all zeros is returned if the term is not present
    ok_(not wrap.get_vector('/c/en/test', oov_vector=False).any())

    # If include_neighbors=True, the neighbor of 'test' in ConceptNet ('trial')
    #  will be used to approximate its vector
    ok_(wrap.get_vector('/c/en/test', oov_vector=True).any())