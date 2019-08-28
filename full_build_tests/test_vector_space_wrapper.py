import os

import pandas as pd
from nose.tools import eq_, ok_, with_setup

from conceptnet5.vectors.query import VectorSpaceWrapper

DATA = os.environ.get("CONCEPTNET_BUILD_DATA", "testdata")
TEST_FRAME = None


def setup_simple_frame():
    data = [
        [4, 4, 4],
        [1, 1, 1],
        [1, 2, 10],
        [3, 3, 4],
        [2, 3, 4],
        [2, 3, 5],
        [7, 2, 7],
        [3, 8, 2],
    ]

    index = [
        'island',
        'Island',
        'cat',
        'figure',
        'figure skating',
        'figure skater',
        'thing',
        '17',
    ]
    global TEST_FRAME
    TEST_FRAME = pd.DataFrame(data=data, index=index)


def setup_multiling_frame():
    data = [[8, 10, 3], [4, 5, 6], [4, 4, 5], [10, 6, 12], [10, 7, 11], [20, 20, 7]]
    index = [
        '/c/pl/kombinacja',
        '/c/en/ski_jumping',
        '/c/en/nordic_combined',
        '/c/en/present',
        '/c/en/gift',
        '/c/en/quiz',
    ]
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

    # test there are no transformations to raw terms other than adding the
    # English tag
    ok_('/c/en/figure skater' in vectors.frame.index)  # no underscore
    ok_('/c/en/Island' in vectors.frame.index)  # no case folding


@with_setup(setup_simple_frame)
def test_englishify():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    eq_(vectors._englishify('/c/sv/harry_potter'), '/c/en/harry_potter')


@with_setup(setup_simple_frame)
def test_match_prefix():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    term = '/c/en/figure_skate'
    expected_prefix_matches = [
        ('/c/en/figure', 0.0033333333333333335),
        ('/c/en/figure skater', 0.0033333333333333335),
        ('/c/en/figure skating', 0.0033333333333333335),
    ]
    prefix_matches = vectors._match_prefix(term=term, prefix_weight=0.01)
    eq_(expected_prefix_matches, prefix_matches)


@with_setup(setup_simple_frame)
def test_index_prefix_range():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    eq_(vectors._index_prefix_range('/c/en/figure'), (3, 6))
    eq_(vectors._index_prefix_range('/c/en/skating'), (0, 0))


@with_setup(setup_multiling_frame)
def test_lookup_neighbors():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    term = '/c/pl/skoki_narciarskie'
    neighbors = vectors._find_neighbors(term=term, limit_per_term=10, weight=1.0)
    expected_neighbors = {
        ('/c/en/ski_jumping', 0.02),
        ('/c/en/ski_jumping', 0.01),
        ('http://pl.dbpedia.org/resource/Skoki_narciarskie', 0.01),
        ('/c/de/skispringen', 0.01),
        ('/c/en/ski_jumping', 0.005),
    }
    eq_(expected_neighbors, set(neighbors))


@with_setup(setup_multiling_frame)
def test_expand_terms():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    term = [('/c/en/ski_jumper', 1.0)]
    expanded_terms = vectors.expand_terms(terms=term, limit_per_term=2, oov_vector=True)

    expected_expanded_terms = [
        ('/c/en/ski_jumper', 0.9523809523809523),
        ('/c/pt/saltadores_de_esqui', 0.019047619047619046),
        ('/c/pl/skoczek_narciarski', 0.019047619047619046),
        ('/c/en/ski_jumping', 0.009523809523809523),
    ]
    eq_(expected_expanded_terms, expanded_terms)


@with_setup(setup_simple_frame)
def test_similar_terms():
    """
    Check if VectorSpaceWrapper's index is sorted and its elements are concepts.
    """
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    ok_(
        '/c/en/figure skating'
        in vectors.similar_terms('/c/en/figure skating', limit=3).index
    )
    ok_(
        '/c/en/figure skater'
        in vectors.similar_terms('/c/en/figure skating', limit=3).index
    )
    ok_('/c/en/figure' in vectors.similar_terms('/c/en/figure skating', limit=3).index)


@with_setup(setup_multiling_frame)
def test_similar_terms_filter():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    ok_(
        '/c/pl/kombinacja'
        in vectors.similar_terms('/c/en/nordic_combined', filter='/c/pl', limit=1).index
    )

    ok_(
        '/c/en/present'
        in vectors.similar_terms('/c/en/gift', filter='/c/en/present', limit=1).index
    )


@with_setup(setup_multiling_frame)
def test_missing_language():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()

    # The frame contains no Esperanto, of course, so the out-of-vocabulary
    # mechanism will fail. We should simply get no results, not crash.
    similarity = vectors.similar_terms('/c/eo/ekzemplo')
    eq_(len(similarity), 0)


@with_setup(setup_multiling_frame)
def test_cache_with_oov():
    vectors = VectorSpaceWrapper(frame=TEST_FRAME)
    vectors.load()
    # check the vector of all zeros is returned if the term is not present
    ok_(not vectors.get_vector('/c/en/test', oov_vector=False).any())

    # If include_neighbors=True, the neighbor of 'test' in ConceptNet ('trial')
    #  will be used to approximate its vector
    ok_(vectors.get_vector('/c/en/test', oov_vector=True).any())
