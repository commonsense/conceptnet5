from conceptnet5.vectors.debias import (
    FEMALE_WORDS, MALE_WORDS, get_category_axis, get_vocabulary_vectors
)
from conceptnet5.vectors.query import VectorSpaceWrapper
from conceptnet5.vectors import standardized_uri
import numpy as np
import pandas as pd
import scipy

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

STEREOTYPE_TARGETS = (
    ['american', 'asian', 'black', 'british', 'chinese', 'jewish', 'mexican', 'muslim', 'nigerian', 'white'],
    ['overweight', 'slut', 'criminal', 'wanker', 'inferior', 'greedy', 'illegal', 'terror', 'scam', 'elegant']
)


def measure_bias(frame):
    vsw = VectorSpaceWrapper(frame=frame)
    vsw.load()

    gender_binary_axis = get_category_axis(frame, FEMALE_WORDS) - get_category_axis(frame, MALE_WORDS)
    gender_bias_numbers = []
    for female_biased_word, male_biased_word in GENDER_BIAS_PAIRS:
        female_biased_uri = standardized_uri('en', female_biased_word)
        male_biased_uri = standardized_uri('en', male_biased_word)
        f_sim = vsw.get_vector(female_biased_uri).dot(gender_binary_axis)
        m_sim = vsw.get_vector(male_biased_uri).dot(gender_binary_axis)
        gender_bias_numbers.append(f_sim - m_sim)

    mean = np.mean(gender_bias_numbers)
    sem = scipy.stats.sem(gender_bias_numbers)
    gender_bias = pd.Series(
        [mean, mean + sem * 2, mean - sem * 2],
        index=['bias', 'low', 'high']
    )

    stereotype_vecs_1 = get_vocabulary_vectors(frame, STEREOTYPE_TARGETS[0])
    stereotype_vecs_2 = get_vocabulary_vectors(frame, STEREOTYPE_TARGETS[1])
    stereotype_corr = stereotype_vecs_1.dot(stereotype_vecs_2.T)
    ethnic_bias_numbers = []
    for i in range(len(stereotype_vecs_1)):
        bias = stereotype_corr[i, i] - np.mean(stereotype_corr[i])
        ethnic_bias_numbers.append(bias)

    mean = np.mean(ethnic_bias_numbers)
    sem = scipy.stats.sem(ethnic_bias_numbers)
    ethnic_bias = pd.Series(
        [mean, mean - sem * 2, mean + sem * 2],
        index=['bias', 'low', 'high']
    )

    return pd.concat([gender_bias, ethnic_bias], axis=0, keys=['gender', 'ethnicity'])
