import os

import numpy as np
import pandas as pd
import pytest

from conceptnet5.uri import is_term
from conceptnet5.vectors import get_vector
from conceptnet5.vectors.transforms import (
    l1_normalize_columns,
    l2_normalize_rows,
    make_big_frame,
    make_small_frame,
    shrink_and_sort,
    standardize_row_labels,
)


@pytest.fixture
def simple_frame():
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
    return pd.DataFrame(data=data, index=index)


@pytest.fixture
def multi_ling_frame():
    data = [[8, 10, 3], [4, 5, 6], [4, 4, 5], [10, 6, 12], [10, 7, 11], [20, 20, 7]]
    index = [
        '/c/pl/kombinacja',
        '/c/en/ski_jumping',
        '/c/en/nordic_combined',
        '/c/en/present',
        '/c/en/gift',
        '/c/en/quiz',
    ]
    return pd.DataFrame(data=data, index=index)


def test_get_vector(simple_frame):
    assert get_vector(simple_frame, '/c/en/cat').equals(
        get_vector(simple_frame, 'cat', 'en')
    )


def test_standardize_row_labels(simple_frame):
    vec1 = simple_frame.loc['island']
    vec2 = simple_frame.loc['Island']
    vec3 = simple_frame.loc['thing']
    standardized_vectors = standardize_row_labels(simple_frame)

    # Check if all labels are terms
    assert all(is_term(label) for label in standardized_vectors.index)

    # Check if all terms standardized to the same concept are merged
    assert standardized_vectors.index.is_unique
    assert '/c/en/Island' not in standardized_vectors.index
    assert '/c/en/island' in standardized_vectors.index
    assert '/c/en/thing' in standardized_vectors.index
    assert standardized_vectors.loc['/c/en/island'].equals(pd.Series([3.0, 3.0, 3.0]))
    assert not standardized_vectors.loc['/c/en/island'].equals(vec1)
    assert not standardized_vectors.loc['/c/en/island'].equals(vec2)
    assert not standardized_vectors.loc['/c/en/thing'].equals(vec3)

    # Check if numbers are substituted with '#'
    assert '/c/en/##' in standardized_vectors.index


def test_l1_normalize_columns(simple_frame):
    normalized = l1_normalize_columns(simple_frame)
    sums = np.sum(np.abs(normalized))
    for s in sums:
        assert s == pytest.approx(1.0)


def test_l2_normalize_rows(simple_frame):
    vectors = l2_normalize_rows(simple_frame)

    lengths = np.sqrt(np.sum(np.power(vectors, 2), axis='columns'))
    for length in lengths:
        assert length == pytest.approx(1.0)

    # Check if a data frame of all zeros will be normalized to zeros
    frame = pd.DataFrame(np.zeros(shape=(1, 10)))
    frame = l2_normalize_rows(frame)
    lengths = np.sqrt(np.sum(np.power(frame, 2), axis=1))
    assert all(length == 0 for length in lengths)


def test_shrink_and_sort(simple_frame):
    n, k = 3, 2
    shrank = shrink_and_sort(simple_frame, n, k)

    # Check the size of the frame
    assert shrank.shape == (n, k)

    # Check if the frame is l2 normalized
    lengths = np.sqrt(np.sum(np.power(shrank, 2), axis='columns'))
    for length in lengths:
        assert length == pytest.approx(1.0)

    # Check if the index is sorted
    assert shrank.index.is_monotonic_increasing


def test_make_language_frame(multi_ling_frame):
    english_frame = make_big_frame(multi_ling_frame, 'en')
    assert '/c/en/ski_jumping' in english_frame.index
    assert '/c/en/nordic_combined' in english_frame.index
    assert '/c/en/present' in english_frame.index
    assert '/c/en/gift' in english_frame.index
    assert '/c/pl/kombinacja' not in english_frame.index


def test_make_small_frame(multi_ling_frame):
    concepts_to_keep = ['/c/en/ski_jumping', '/c/en/nordic_combined', '/c/en/present']
    small_frame = make_small_frame(multi_ling_frame, concepts_to_keep)
    assert '/c/en/ski_jumping' not in small_frame.index
    assert '/c/en/nordic_combined' not in small_frame.index
    assert '/c/en/present' in small_frame.index
    assert '/c/en/gift' not in small_frame.index
