from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import get_vector, standardized_uri, get_vector, cosine_similarity
from conceptnet5.vectors.query import VectorSpaceWrapper
from statsmodels.stats.proportion import proportion_confint
import numpy as np
import pandas as pd


def read_cloze(filename):
    with open(filename, encoding='utf-8') as file:
        file.readline()  # throw away header
        for line in file:
            if line.rstrip():
                items = line.rstrip().split('\t')
                uuid, sent1, sent2, sent3, sent4, answer1, answer2, answer_num = items
                if answer_num == '1':
                    right_answer = answer1
                    wrong_answer = answer2
                elif answer_num == '2':
                    right_answer = answer2
                    wrong_answer = answer1
                else:
                    raise ValueError("Unrecognized answer number: %r" % answer_num)

                yield ((sent1, sent2, sent3, sent4), (right_answer, wrong_answer))


def evaluate(frame, subset='val'):
    """
    Evaluate a DataFrame containing term vectors on its ability to predict term
    relatedness, according to MEN-3000, RW, MTurk-771, and WordSim-353. Use a
    VectorSpaceWrapper to fill missing vocabulary from ConceptNet.

    Return a Series containing these labeled results.
    """
    # Make subset names consistent with other datasets
    if subset == 'dev':
        subset = 'val'
    elif subset == 'all':
        # for the final evaluation, use just the test data
        subset = 'test'
    filename = get_support_data_filename('story-cloze/cloze_test_spring2016_%s.tsv' % subset)
    vectors = VectorSpaceWrapper(frame=frame)
    total = 0
    correct = 0
    for sentences, answers in read_cloze(filename):
        text = ' '.join(sentences)
        right_answer, wrong_answer = answers
        probe_vec = vectors.text_to_vector('en', text)
        right_vec = vectors.text_to_vector('en', right_answer)
        wrong_vec = vectors.text_to_vector('en', wrong_answer)

        right_sim = cosine_similarity(probe_vec, right_vec)
        wrong_sim = cosine_similarity(probe_vec, wrong_vec)
        if right_sim > wrong_sim:
            correct += 1
        total += 1
        # print("%+4.2f %s / %s / %s" % (right_sim - wrong_sim, text, right_answer, wrong_answer))
    low, high = proportion_confint(correct, total)
    return pd.Series([correct / total, low, high], index=['acc', 'low', 'high'])
