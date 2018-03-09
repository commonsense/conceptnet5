import numpy as np
import os
import pandas as pd
from nose.tools import ok_, eq_, assert_almost_equal, with_setup

from conceptnet5.uri import is_term
from conceptnet5.vectors import get_vector
from conceptnet5.vectors.query import VectorSpaceWrapper
from conceptnet5.vectors.transforms import standardize_row_labels, l1_normalize_columns, \
    l2_normalize_rows, shrink_and_sort

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

    index = ['island', 'Island', 'cat', 'figure', 'figure skating', 'figure skater','thing','17']
    global TEST_FRAME
    TEST_FRAME = pd.DataFrame(data=data, index=index)


def setup_multi_ling_frame():
    data = [[8, 10, 3],
            [4, 5, 6],
            [4, 4, 5],
            [10, 6, 12],
            [10, 7, 11]]
    index = ['/c/pl/kombinacja',
             '/c/en/ski_jumping',
             '/c/en/nordic_combined',
             '/c/en/present',
             '/c/en/gift']
    global TEST_FRAME
    TEST_FRAME = pd.DataFrame(data=data, index=index)


@with_setup(setup_simple_frame)
def test_get_vector():
    ok_(get_vector(TEST_FRAME, '/c/en/cat').equals(get_vector(TEST_FRAME, 'cat', 'en')))


@with_setup(setup_simple_frame())
def test_vector_space_wrapper():
    """
    Check if VectorSpaceWrapper's index is sorted and its elements are concepts.
    """
    wrap = VectorSpaceWrapper(frame=TEST_FRAME)
    wrap.load()
    ok_(all(is_term(label) for label in wrap.frame.index))
    ok_(wrap.frame.index.is_monotonic_increasing)

    # test there are no transformations to raw terms other than adding the english tag
    ok_('/c/en/figure skater' in wrap.frame.index) # no underscore
    ok_('/c/en/Island' in wrap.frame.index) # no case folding

    # test index_prefix_range
    ok_(wrap.index_prefix_range('/c/en/figure') == (3, 6))
    ok_(wrap.index_prefix_range('/c/en/skating') == (0, 0))

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


@with_setup(setup_simple_frame)
def test_standardize_row_labels():
    vec1 = TEST_FRAME.loc['island']
    vec2 = TEST_FRAME.loc['Island']
    vec3 = TEST_FRAME.loc['thing']
    standardized_vectors = standardize_row_labels(TEST_FRAME)

    # Check if all labels are terms
    ok_(all(is_term(label) for label in standardized_vectors.index))

    # Check if all terms standardized to the same concept are merged
    ok_(standardized_vectors.index.is_unique)
    ok_('/c/en/Island' not in standardized_vectors.index)
    ok_('/c/en/island' in standardized_vectors.index)
    ok_('/c/en/thing' in standardized_vectors.index)
    ok_(standardized_vectors.loc['/c/en/island'].equals(pd.Series([3.0, 3.0, 3.0])))
    ok_(not standardized_vectors.loc['/c/en/island'].equals(vec1))
    ok_(not standardized_vectors.loc['/c/en/island'].equals(vec2))
    ok_(not standardized_vectors.loc['/c/en/thing'].equals(vec3))

    # Check if numbers are substituted with '#'
    ok_('/c/en/##' in standardized_vectors.index)


@with_setup(setup_simple_frame)
def test_l1_normalize_columns():
    normalized = l1_normalize_columns(TEST_FRAME)
    sums = np.sum(np.abs(normalized))
    for s in sums:
        assert_almost_equal(s, 1.0, places=4)


@with_setup(setup_simple_frame)
def test_l2_normalize_rows():
    vectors = l2_normalize_rows(TEST_FRAME)

    lengths = np.sqrt(np.sum(np.power(vectors, 2), axis='columns'))
    for length in lengths:
        assert_almost_equal(length, 1.0, places=4)

    # Check if a data frame of all zeros will be normalized to zeros
    frame = pd.DataFrame(np.zeros(shape=(1, 10)))
    frame = l2_normalize_rows(frame)
    lengths = np.sqrt(np.sum(np.power(frame, 2), axis=1))
    ok_(all(length == 0 for length in lengths))


@with_setup(setup_simple_frame)
def test_shrink_and_sort():

    n, k = 3, 2
    shrank = shrink_and_sort(TEST_FRAME, n, k)

    # Check the size of the frame
    ok_(shrank.shape == (n, k))

    # Check if the frame is l2 normalized
    lengths = np.sqrt(np.sum(np.power(shrank, 2), axis='columns'))
    for length in lengths:
        assert_almost_equal(length, 1.0, places=4)

    # Check if the index is sorted
    ok_(shrank.index.is_monotonic_increasing)
