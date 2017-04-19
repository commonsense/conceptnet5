import os
from math import isclose

import click
import numpy as np
import pandas as pd
from nose.tools import eq_, ok_

from conceptnet5 import vectors
from conceptnet5.vectors.evaluation.compare import load_any_embeddings
from conceptnet5.vectors.query import VectorSpaceWrapper
from conceptnet5.vectors.transforms import standardize_row_labels, l1_normalize_columns, \
    l2_normalize_rows, shrink_and_sort, miniaturize

DATA = os.environ.get("CONCEPTNET_BUILD_DATA")


def test_get_vectors(frame=None):
    """
     Check if vectors.get_vector() returns the same vector given lables that are shaped in a
     different way.
    """
    if frame:
        frame = load_any_embeddings(frame)
        ok_(vectors.get_vector(frame, '/c/en/cat').equals(vectors.get_vector(frame, 'cat', 'en')))

    frame = load_any_embeddings(DATA + '/precomputed/vectors/numberbatch.h5')
    ok_(vectors.get_vector(frame, '/c/en/cat').equals(vectors.get_vector(frame, 'cat', 'en')))

    frame = load_any_embeddings(DATA + '/raw/vectors/GoogleNews-vectors-negative300.bin.gz')
    ok_(vectors.get_vector(frame, '/c/en/cat').equals(vectors.get_vector(frame, 'cat', 'en')))


def test_terms_in_frame(frame=None):
    if frame:
        vectors = load_any_embeddings(frame)
    else:
        vectors = load_any_embeddings(DATA + '/precomputed/vectors/numberbatch.h5')

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
        wrap.load() # TODO change all of these to all, not only index[0]
        assert wrap.frame.index[0].startswith('/c')
        assert wrap.frame.index.is_monotonic_increasing

    # Load a VSW from a filename
    vector_filename = DATA + '/vectors/w2v-google-news.h5'
    wrap = VectorSpaceWrapper(vector_filename=vector_filename)
    wrap.load()
    assert wrap.frame.index[0].startswith('/c')
    assert wrap.frame.index.is_monotonic_increasing

    # Load a VSW from a frame
    frame = load_any_embeddings(DATA + '/raw/vectors/GoogleNews-vectors-negative300.bin.gz')
    wrap = VectorSpaceWrapper(frame=frame)
    wrap.load()
    assert wrap.frame.index[0].startswith('/c')
    assert wrap.frame.index.is_monotonic_increasing

    # Load a VSW from vectors/mini.h5
    wrap = VectorSpaceWrapper()
    wrap.load()
    assert wrap.frame.index[0].startswith('/c')
    assert wrap.frame.index.is_monotonic_increasing


def test_standarize_row_labels():
    frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    frame = load_any_embeddings(frame)

    word1 = 'google'
    word2 = 'Google'
    word3 = 'UTM-1'
    word4 = 'archipelagoes'
    vec1 = frame.loc[word1]
    vec2 = frame.loc[word2]
    vec3 = frame.loc[word3]
    vec4 = frame.loc[word4]
    frame_std = standardize_row_labels(frame)

    # Check if all labels are concepts
    assert all(label.startswith('/c/') for label in frame_std.index)

    # Check if all terms standardized to the same concept are merged
    assert frame_std.index.is_unique
    assert '/c/en/Google' not in frame_std.index
    assert not frame_std.loc['/c/en/google'].equals(vec1)
    assert not frame_std.loc['/c/en/google'].equals(vec2)

    # Check if lemmatization changes the value of a concept
    assert not frame_std.loc['/c/en/archipelagoes'].equals(vec4)

    # Check if numbers are substituted with '#'
    # assert not '/c/en/utm_1' in frame_std.index
    # assert frame_std.loc['/c/en/utm_#'].equals(vec3)


def test_l1_normalize_columns():
    frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    frame = load_any_embeddings(frame)
    frame = l1_normalize_columns(frame)
    sums = np.sum(np.abs(frame))

    ok_(all(isclose(s, 1.0) for s in sums))


def test_l2_normalize_rows():
    frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    frame = load_any_embeddings(frame)
    frame = l2_normalize_rows(frame)
    lengths = np.sqrt(np.sum(np.power(frame, 2), axis='columns'))
    ok_(all(isclose(length, 1.0) for length in lengths))

    # Check if a dataframe of all zeroes will be normalized to NaN
    frame = pd.DataFrame(np.zeros(shape=(1, 10)))
    frame = l2_normalize_rows(frame)
    lengths = np.sqrt(np.sum(np.power(frame, 2), axis=1))
    ok_(all(np.isnan(length) for length in lengths))


def test_shrink_and_sort():
    frame = DATA + '/raw/vectors/glove12.840B.300d.txt.gz'
    frame = load_any_embeddings(frame)
    n, k = 10, 20
    shrinked = shrink_and_sort(frame, n, k)

    # Check the size of the frame
    ok_(shrinked.shape == (n, k))

    # Check if the frame is l2 normalized
    lengths = np.sqrt(np.sum(np.power(shrinked, 2), axis='columns'))
    ok_(all(isclose(length, 1.0) for length in lengths))

    # Check if the index is sorted
    ok_(shrinked.index.is_monotonic_increasing)


def test_miniturized():
    frame = DATA + '/vectors/numberbatch.h5'
    frame = load_any_embeddings(frame)
    orig_shape = frame.shape
    mini = miniaturize(frame)

    # Check if the frame is smaller
    new_shape = mini.shape
    ok_(orig_shape[0] > new_shape[0] and orig_shape[1] > new_shape[1])

    # Check if the frame is l2 normalized
    lengths = np.sqrt(np.sum(np.power(mini, 2), axis='columns'))
    # ok_(all(isclose(length, 1.0) for length in lengths))

    # Check if the index is sorted
    ok_(mini.index.is_monotonic_increasing)


@click.command()
@click.argument('frame')
def test(frame):
    # test_replace_numbers()
    # test_standardized_uri()
    test_terms_in_frame(frame)
    test_vector_space_wrapper()
    test_get_vectors()
    test_standarize_row_labels()
    test_l1_normalize_columns()
    test_l2_normalize_rows()
    test_shrink_and_sort()
    test_miniturized()


if __name__ == '__main__':
    test()
