import os

import click
import numpy as np
import pandas as pd
from nose.tools import ok_, eq_, assert_almost_equal

from conceptnet5.vectors import get_vector
from conceptnet5.vectors.evaluation.compare import load_any_embeddings
from conceptnet5.vectors.query import VectorSpaceWrapper
from conceptnet5.vectors.transforms import standardize_row_labels, l1_normalize_columns, \
    l2_normalize_rows, shrink_and_sort

DATA = os.environ.get("CONCEPTNET_BUILD_DATA", "testdata")


def test_get_vector(frame=None):
    """
    Check if vectors.get_vector() returns the same vector given labels that are shaped in a
    different way.
    """
    if frame:
        vectors = load_any_embeddings(frame)
        ok_(get_vector(vectors, '/c/en/cat').equals(get_vector(vectors, 'cat', 'en')))

    vectors = load_any_embeddings(DATA + '/vectors/glove12-840B.h5')
    ok_(get_vector(vectors, '/c/en/cat').equals(get_vector(vectors, 'cat', 'en')))


def test_vector_space_wrapper(frame=None):
    """
    Check if VectorSpaceWrapper's index is sorted and its elements are concepts.
    """

    # Load a VSW from a user-supplied frame
    if frame:
        frame = load_any_embeddings(frame)
        wrap = VectorSpaceWrapper(frame=frame)
        wrap.load()
        ok_(all(label.startswith('/c') for label in wrap.frame.index[1:]))
        ok_(wrap.frame.index.is_monotonic_increasing)

    # Load a VSW from a filename
    vector_filename = DATA + '/vectors/glove12-840B.h5'
    wrap = VectorSpaceWrapper(vector_filename=vector_filename)
    wrap.load()
    ok_(all(label.startswith('/c') for label in wrap.frame.index[1:]))
    ok_(wrap.frame.index.is_monotonic_increasing)

    # Load a VSW from a frame
    frame = load_any_embeddings(DATA + '/vectors/glove12-840B.h5')
    wrap = VectorSpaceWrapper(frame=frame)
    wrap.load()
    ok_(all(label.startswith('/c') for label in wrap.frame.index[1:]))
    ok_(wrap.frame.index.is_monotonic_increasing)


def test_standardize_row_labels(frame=None):
    if not frame:
        frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    vectors = load_any_embeddings(frame)

    vec1 = vectors.loc['island']
    vec2 = vectors.loc['Island']
    vec3 = vectors.loc['things']
    standardized_vectors = standardize_row_labels(vectors)

    # Check if all labels are concepts
    ok_(all(label.startswith('/c') for label in standardized_vectors.index[1:]))

    # Check if all terms standardized to the same concept are merged
    ok_(standardized_vectors.index.is_unique)
    ok_('/c/en/Island' not in standardized_vectors.index)
    ok_('/c/en/island' in standardized_vectors.index)
    ok_('/c/en/thing' in standardized_vectors.index)
    ok_(not standardized_vectors.loc['/c/en/island'].equals(vec1))
    ok_(not standardized_vectors.loc['/c/en/island'].equals(vec2))
    ok_(not standardized_vectors.loc['/c/en/things'].equals(vec3))

    # Check if numbers are substituted with '#'
    ok_('/c/en/##' in standardized_vectors.index)


def test_l1_normalize_columns(frame=None):
    if not frame:
        frame = DATA + '/vectors/glove12-840B.h5'
    vectors = load_any_embeddings(frame)

    vectors = l1_normalize_columns(vectors)
    sums = np.sum(np.abs(vectors))
    for s in sums:
        assert_almost_equal(s, 1.0, places=4)


def test_l2_normalize_rows(frame=None):
    if not frame:
        frame = DATA + '/vectors/glove12-840B.h5'
    vectors = load_any_embeddings(frame)

    vectors = l2_normalize_rows(vectors)

    lengths = np.sqrt(np.sum(np.power(vectors, 2), axis='columns'))
    for length in lengths:
        assert_almost_equal(length, 1.0, places=4)

    # Check if a data frame of all zeroes will be normalized to NaN
    frame = pd.DataFrame(np.zeros(shape=(1, 10)))
    frame = l2_normalize_rows(frame)
    lengths = np.sqrt(np.sum(np.power(frame, 2), axis=1))
    ok_(all(np.isnan(length) for length in lengths))


def test_shrink_and_sort(frame=None):
    if not frame:
        frame = DATA + '/vectors/glove12-840B.h5'
    vectors = load_any_embeddings(frame)

    n, k = 10, 20
    shrank = shrink_and_sort(vectors, n, k)

    # Check the size of the frame
    ok_(shrank.shape == (n, k))

    # Check if the frame is l2 normalized
    lengths = np.sqrt(np.sum(np.power(shrank, 2), axis='columns'))
    for length in lengths:
        assert_almost_equal(length, 1.0, places=4)

    # Check if the index is sorted
    ok_(shrank.index.is_monotonic_increasing)


@click.command()
@click.option('--frame', default=None)
def test(frame):
    test_vector_space_wrapper(frame)
    test_get_vector(frame)
    test_standardize_row_labels(frame)
    test_l1_normalize_columns(frame)
    test_l2_normalize_rows(frame)
    test_shrink_and_sort(frame)


if __name__ == '__main__':
    test()
