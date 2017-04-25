import os
from math import isclose

import click
import numpy as np
import pandas as pd
from nose.tools import ok_

from conceptnet5.vectors import get_vector
from conceptnet5.vectors.evaluation.compare import load_any_embeddings
from conceptnet5.vectors.query import VectorSpaceWrapper
from conceptnet5.vectors.transforms import standardize_row_labels, l1_normalize_columns, \
    l2_normalize_rows, shrink_and_sort, miniaturize

DATA = os.environ.get("CONCEPTNET_BUILD_DATA")


def test_get_vector(frame=None):
    """
     Check if vectors.get_vector() returns the same vector given labels that are shaped in a
     different way.
    """
    if frame:
        vectors = load_any_embeddings(frame)
        ok_(get_vector(vectors, '/c/en/cat').equals(get_vector(vectors, 'cat', 'en')))

    vectors = load_any_embeddings(DATA + '/precomputed/vectors/numberbatch.h5')
    ok_(get_vector(vectors, '/c/en/cat').equals(get_vector(vectors, 'cat', 'en')))

    vectors = load_any_embeddings(DATA + '/raw/vectors/GoogleNews-vectors-negative300.bin.gz')
    ok_(get_vector(vectors, '/c/en/cat').equals(get_vector(vectors, 'cat', 'en')))


def test_terms_in_frame(frame=None):
    """
    Check if these terms are in vector's index
    """
    if not frame:
        frame = DATA + '/vectors/numberbatch.h5'
    vectors = load_any_embeddings(frame)

    ok_('/c/en/semantics' in vectors.index)
    ok_('/c/en/derived' in vectors.index)
    ok_('/c/en/automatically' in vectors.index)
    ok_('/c/en/from' in vectors.index)
    ok_('/c/en/language' in vectors.index)
    ok_('/c/en/corpora' in vectors.index)
    ok_('/c/en/contain' in vectors.index)
    ok_('/c/en/human' in vectors.index)
    ok_('/c/en/biases' in vectors.index)


def test_vector_space_wrapper(frame=None):
    """
    Check if VectorSpaceWrapper's index is sorted and its elements are concepts.
    """

    # Load a VSW from a user-supplied frame
    if frame:
        frame = load_any_embeddings(frame)
        wrap = VectorSpaceWrapper(frame=frame)
        wrap.load()
        ok_(all(label.startswith('/c') for label in wrap.frame.index))
        ok_(wrap.frame.index.is_monotonic_increasing)

    # Load a VSW from a filename
    vector_filename = DATA + '/vectors/w2v-google-news.h5'
    wrap = VectorSpaceWrapper(vector_filename=vector_filename)
    wrap.load()
    ok_(all(label.startswith('/c') for label in wrap.frame.index))
    ok_(wrap.frame.index.is_monotonic_increasing)

    # Load a VSW from a frame
    frame = load_any_embeddings(DATA + '/raw/vectors/GoogleNews-vectors-negative300.bin.gz')
    wrap = VectorSpaceWrapper(frame=frame)
    wrap.load()
    ok_(all(label.startswith('/c') for label in wrap.frame.index))
    ok_(wrap.frame.index.is_monotonic_increasing)

    # Load a VSW of vectors/mini.h5
    wrap = VectorSpaceWrapper()
    wrap.load()
    ok_(all(label.startswith('/c') for label in wrap.frame.index))
    ok_(wrap.frame.index.is_monotonic_increasing)


def test_standardize_row_labels(frame=None):
    if not frame:
        frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    vectors = load_any_embeddings(frame)

    word1 = 'island'
    word2 = 'Island'
    word3 = 'archipelagos'
    vec1 = vectors.loc[word1]
    vec2 = vectors.loc[word2]
    vec3 = vectors.loc[word3]
    standardized_vectors = standardize_row_labels(vectors)

    # Check if all labels are concepts
    ok_(all(label.startswith('/c/') for label in standardized_vectors.index))

    # Check if all terms standardized to the same concept are merged
    ok_(standardized_vectors.index.is_unique)
    ok_('/c/en/Island' not in standardized_vectors.index)
    ok_(not standardized_vectors.loc['/c/en/island'].equals(vec1))
    ok_(not standardized_vectors.loc['/c/en/island'].equals(vec2))

    # Check if lemmatization changes the value of a concept
    ok_(not standardized_vectors.loc['/c/en/archipelagos'].equals(vec3))

    # Check if numbers are substituted with '#'
    ok_('/c/en/utc_##' in standardized_vectors.index)


def test_l1_normalize_columns(frame=None):
    if not frame:
        frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    vectors = load_any_embeddings(frame)

    vectors = l1_normalize_columns(vectors)
    sums = np.sum(np.abs(vectors))
    ok_(all(isclose(s, 1.0) for s in sums))


def test_l2_normalize_rows(frame=None):
    if not frame:
        frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    vectors = load_any_embeddings(frame)

    vectors = l2_normalize_rows(vectors)

    lengths = np.sqrt(np.sum(np.power(vectors, 2), axis='columns'))
    ok_(all(isclose(length, 1.0) for length in lengths))

    # Check if a dataframe of all zeroes will be normalized to NaN
    frame = pd.DataFrame(np.zeros(shape=(1, 10)))
    frame = l2_normalize_rows(frame)
    lengths = np.sqrt(np.sum(np.power(frame, 2), axis=1))
    ok_(all(np.isnan(length) for length in lengths))


def test_shrink_and_sort(frame=None):
    if not frame:
        frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    vectors = load_any_embeddings(frame)

    n, k = 10, 20
    shrinked = shrink_and_sort(vectors, n, k)

    # Check the size of the frame
    ok_(shrinked.shape == (n, k))

    # Check if the frame is l2 normalized
    lengths = np.sqrt(np.sum(np.power(shrinked, 2), axis='columns'))
    ok_(all(isclose(length, 1.0) for length in lengths))

    # Check if the index is sorted
    ok_(shrinked.index.is_monotonic_increasing)


def test_miniturize(frame=None):
    if not frame:
        frame = DATA + '/vectors/numberbatch.h5'
    frame = load_any_embeddings(frame)

    orig_shape = frame.shape
    prefix = '/c/pt'
    mini = miniaturize(frame, prefix=prefix)

    # Check if the frame is smaller
    new_shape = mini.shape
    ok_(orig_shape[0] > new_shape[0] and orig_shape[1] > new_shape[1])

    # Check if the index is sorted
    ok_(mini.index.is_monotonic_increasing)

    # Check if the labels are only of a language specified.
    ok_(all(label.startswith(prefix) for label in mini.index))


@click.command()
@click.argument('frame')
def test(frame):
    test_terms_in_frame(frame)
    test_vector_space_wrapper(frame)
    test_get_vector(frame)
    test_standardize_row_labels(frame)
    test_l1_normalize_columns(frame)
    test_l2_normalize_rows(frame)
    test_shrink_and_sort(frame)
    test_miniturize(frame)


if __name__ == '__main__':
    test()
