import numpy as np
import os
import pandas as pd
from nose.tools import ok_, assert_almost_equal

from conceptnet5.uri import is_term
from conceptnet5.vectors import get_vector
from conceptnet5.vectors.query import VectorSpaceWrapper
from conceptnet5.vectors.transforms import standardize_row_labels, l1_normalize_columns, \
    l2_normalize_rows, shrink_and_sort

DATA = os.environ.get("CONCEPTNET_BUILD_DATA", "testdata")
TEST_FRAME = None


def setup():
    data = [[4, 4, 4],
            [1, 1, 1],
            [1, 2, 10],
            [3, 3, 4],
            [2, 3, 4],
            [2, 3, 5],
            [7, 2, 7],
            [3, 8, 2]]

    index = ['island',
            'Island',
            'cat',
             'figure',
             'figure skating',
             'figure skater',
            'thing',
            '17']
    global TEST_FRAME
    TEST_FRAME = pd.DataFrame(data=data, index=index)


def test_get_vector():
    setup()
    ok_(get_vector(TEST_FRAME, '/c/en/cat').equals(get_vector(TEST_FRAME, 'cat', 'en')))


def test_vector_space_wrapper():
    """
    Check if VectorSpaceWrapper's index is sorted and its elements are concepts.
    """
    setup()
    wrap = VectorSpaceWrapper(frame=TEST_FRAME)
    wrap.load()
    ok_(all(is_term(label) for label in wrap.frame.index))
    ok_(wrap.frame.index.is_monotonic_increasing)

    # test index_prefix_range
    ok_(wrap.index_prefix_range('/c/en/figure') == (2, 5))
    ok_(wrap.index_prefix_range('/c/en/skating') == (0, 0))

    # test_similar_terms
    ok_('/c/en/figure_skating' in wrap.similar_terms('/c/en/figure_skating', limit=3).index)
    ok_('/c/en/figure_skater' in wrap.similar_terms('/c/en/figure_skating', limit=3).index)
    ok_('/c/en/figure' in wrap.similar_terms('/c/en/figure_skating', limit=3).index)


def test_standardize_row_labels():
    setup()
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


def test_l1_normalize_columns():
    setup()
    normalized = l1_normalize_columns(TEST_FRAME)
    sums = np.sum(np.abs(normalized))
    for s in sums:
        assert_almost_equal(s, 1.0, places=4)


def test_l2_normalize_rows():
    setup()
    vectors = l2_normalize_rows(TEST_FRAME)

    lengths = np.sqrt(np.sum(np.power(vectors, 2), axis='columns'))
    for length in lengths:
        assert_almost_equal(length, 1.0, places=4)

    # Check if a data frame of all zeros will be normalized to zeros
    frame = pd.DataFrame(np.zeros(shape=(1, 10)))
    frame = l2_normalize_rows(frame)
    lengths = np.sqrt(np.sum(np.power(frame, 2), axis=1))
    ok_(all(length == 0 for length in lengths))


def test_shrink_and_sort():
    setup()

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


def test():
    test_vector_space_wrapper()
    test_get_vector()
    test_standardize_row_labels()
    test_l1_normalize_columns()
    test_l2_normalize_rows()
    test_shrink_and_sort()


if __name__ == '__main__':
    test()
