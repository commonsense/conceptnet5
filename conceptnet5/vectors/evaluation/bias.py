import numpy as np
import pandas as pd
import scipy

from conceptnet5.vectors import standardized_uri, normalize_vec
from conceptnet5.vectors.transforms import l2_normalize_rows
from conceptnet5.vectors.debias import (FEMALE_WORDS, MALE_WORDS,
                                        PEOPLE_BY_BELIEF, PEOPLE_BY_ETHNICITY,
                                        get_category_axis,
                                        get_vocabulary_vectors)
from conceptnet5.vectors.query import VectorSpaceWrapper

# Pairs rated as "biased" at least 3 times as often as "appropriate", and
# at least twice overall, in Bolukbasi et al.:
# https://arxiv.org/pdf/1607.06520.pdf
GENDER_BIAS_PAIRS = [
    ('midwife', 'doctor'),
    ('sewing', 'carpentry'),
    ('pediatrician', 'orthopedic surgeon'),
    ('registered nurse', 'physician'),
    ('housewife', 'shopkeeper'),
    ('skirts', 'shorts'),
    ('nurse', 'surgeon'),
    ('interior designer', 'architect'),
    ('blond', 'burly'),
    ('nanny', 'chauffeur'),
    ('feminism', 'conservatism'),
    ('adorable', 'goofy'),
    ('vocalists', 'guitarists'),
    ('cosmetics', 'pharmaceuticals'),
    ('whore', 'coward'),
    ('vocalist', 'guitarist'),
    ('petite', 'lanky'),
    ('sassy', 'snappy'),
    ('charming', 'affable'),
    ('giggle', 'chuckle'),
    ('witch', 'demon'),
    ('volleyball', 'football'),
    ('feisty', 'mild mannered'),
    ('cupcakes', 'pizzas'),
    ('dolls', 'replicas'),
    ('netball', 'rugby'),
    ('glamorous', 'flashy'),
    ('sweater', 'jersey'),
    ('feminist', 'liberal'),
    ('rebounder', 'playmaker'),
    ('nude', 'shirtless'),
    ('judgmental', 'arrogant'),
    ('lovely', 'brilliant'),
    ('practicality', 'durability'),
    ('singer', 'frontman'),
    ('violinist', 'virtuoso'),
    ('beautiful', 'majestic'),
    ('sexism', 'racism'),
    ('pink', 'red'),
    ('hysterical', 'comical'),
    ('beauty', 'grandeur'),
    ('cheerful', 'jovial')
]

# This intentionally is a slightly different list than the one in debias.py.
# We need to test associations with more terms than the ones we specifically
# corrected.
STEREOTYPE_TERMS = [
    'cheap', 'criminal', 'dumb', 'elegant', 'evil', 'genius', 'greedy',
    'hooligan', 'illegal', 'inferior', 'lazy', 'overweight', 'power',
    'scammer', 'sexy', 'slave', 'slob', 'slut', 'terrorist', 'wanker'
]


def correlation_bias(vecs1, vecs2):
    bias_numbers = []
    bias_vecs1 = l2_normalize_rows(
        pd.DataFrame(vecs1 - np.mean(vecs1, axis=0))
    ).values
    bias_vecs2 = l2_normalize_rows(
        pd.DataFrame(vecs2 - np.mean(vecs2, axis=0))
    ).values
    grid = bias_vecs1.dot(bias_vecs2.T)
    for i in range(grid.shape[1]):
        col_bias = np.max(grid[:, i]) - np.mean(grid[:, i])
        # col_bias = np.std(grid[:, i]) / np.std(background[:, i])
        bias_numbers.append(col_bias)

    mean = np.mean(bias_numbers)
    sem = scipy.stats.sem(bias_numbers)
    return pd.Series(
        [mean, mean - sem * 2, mean + sem * 2],
        index=['bias', 'low', 'high']
    )


def measure_bias(frame):
    vsw = VectorSpaceWrapper(frame=frame)
    vsw.load()

    gender_binary_axis = normalize_vec(get_category_axis(frame, FEMALE_WORDS) - get_category_axis(frame, MALE_WORDS))
    gender_bias_numbers = []
    for female_biased_word, male_biased_word in GENDER_BIAS_PAIRS:
        female_biased_uri = standardized_uri('en', female_biased_word)
        male_biased_uri = standardized_uri('en', male_biased_word)
        diff = normalize_vec(vsw.get_vector(female_biased_uri) - vsw.get_vector(male_biased_uri)).dot(gender_binary_axis)
        gender_bias_numbers.append(diff)

    mean = np.mean(gender_bias_numbers)
    sem = scipy.stats.sem(gender_bias_numbers)
    gender_bias = pd.Series(
        [mean, mean - sem * 2, mean + sem * 2],
        index=['bias', 'low', 'high']
    )

    stereotype_vecs_1 = get_vocabulary_vectors(frame, PEOPLE_BY_ETHNICITY)
    stereotype_vecs_2 = get_vocabulary_vectors(frame, STEREOTYPE_TERMS)
    ethnic_bias = correlation_bias(stereotype_vecs_1, stereotype_vecs_2)

    stereotype_vecs_1 = get_vocabulary_vectors(frame, PEOPLE_BY_BELIEF)
    stereotype_vecs_2 = get_vocabulary_vectors(frame, STEREOTYPE_TERMS)
    belief_bias = correlation_bias(stereotype_vecs_1, stereotype_vecs_2)

    return pd.DataFrame({
        'gender': gender_bias,
        'ethnicity': ethnic_bias,
        'beliefs': belief_bias
    }).T
