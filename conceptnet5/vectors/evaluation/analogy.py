from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import standardized_uri, get_vector, similar_to_vec
from conceptnet5.vectors.query import VectorSpaceWrapper
from statsmodels.stats.proportion import proportion_confint
import wordfreq
import numpy as np
import pandas as pd


def read_google_analogies(filename):
    """
    Read the 'questions-words.txt' file that comes with the word2vec package.
    """
    quads = [
        [standardized_uri('en', term) for term in line.rstrip().split(' ')]
        for line in open(filename, encoding='utf-8')
        if not line.startswith(':')
    ]
    return quads


def read_turney_analogies(filename):
    """
    Read Turney and Littman's dataset of SAT analogy questions. This data
    requires permission to redistribute, so you have to ask Peter Turney
    for the file.
    """
    questions = []
    question_lines = []
    with open(filename, encoding='utf-8') as file:
        for line in file:
            line = line.rstrip()
            if line and not line.startswith('#'):
                if len(line) == 1:
                    # A single letter on a line indicates the answer to a question.
                    answer_index = ord(line) - ord('a')

                    # Line 0 is a header we can discard.
                    raw_pairs = [qline.split(' ')[:2] for qline in question_lines[1:]]
                    concept_pairs = [tuple(standardized_uri('en', term) for term in pair) for pair in raw_pairs]

                    # The first of the pairs we got is the prompt pair. The others are
                    # answers (a) through (e).
                    questions.append((concept_pairs[0], concept_pairs[1:], answer_index))
                    question_lines.clear()
                else:
                    question_lines.append(line)
    return questions


def analogy_func(frame, a1, b1, a2):
    return get_vector(frame, b1) - get_vector(frame, a1) + get_vector(frame, a2)


def pairwise_analogy_func(wrap, a1, b1, a2, b2, weights=(0.65, 1.35, 1)):
    va1 = wrap.get_vector(a1)
    vb1 = wrap.get_vector(b1)
    va2 = wrap.get_vector(a2)
    vb2 = wrap.get_vector(b2)

    value = (
        weights[0] * (va1.dot(vb1) + va2.dot(vb2)) +
        weights[1] * (va1.dot(va2) + vb1.dot(vb2)) -
        weights[2] * (vb1.dot(va2) + va1.dot(vb2))
    )
    return value


def eval_pairwise_analogies(frame, eval_filename, subset='all',
                            weights=(0.65, 1.35, 1)):
    total = 0
    correct = 0
    wrap = VectorSpaceWrapper(frame=frame)
    for idx, (prompt, choices, answer) in enumerate(read_turney_analogies(eval_filename)):
        # Enable an artificial training/test split
        if subset == 'all' or (subset == 'dev') == (idx % 2 == 0):
            a1, b1 = prompt
            choice_values = []
            for choice in choices:
                a2, b2 = choice
                choice_values.append(
                    pairwise_analogy_func(wrap, a1, b1, a2, b2, weights)
                )
            our_answer = np.argmax(choice_values)
            if our_answer == answer:
                correct += 1
            total += 1
    low, high = proportion_confint(correct, total)
    return pd.Series([correct / total, low, high], index=['acc', 'low', 'high'])


def tune_pairwise_analogies(frame, eval_filename, subset):
    """
    Our pairwise analogy function has three weights that can be tuned
    (and therefore two free parameters, as the total weight does not matter).

    This function holds out half of the data and grid-searches for the best
    combination of parameters, then evaluates on the other half of the data.
    """
    weights = [0.5, 0.6, 2/3, 0.7, 0.75, 0.8, 0.9, 1.0,
               1.1, 1.2, 1.25, 1.3, 4/3, 1.4, 1.5]

    best_weights = None
    best_acc = 0.
    for weight_a in weights:
        for weight_b in weights:
            weight_tuple = (weight_a, weight_b, 1.)
            acc = eval_pairwise_analogies(
                frame, eval_filename, subset='dev',
                weights=weight_tuple
            ).loc['acc']
            if acc > best_acc:
                print(weight_tuple, acc)
                best_weights = weight_tuple
                best_acc = acc
    print()
    return eval_pairwise_analogies(
        frame, eval_filename, subset=subset, weights=best_weights
    )


def eval_analogies(frame):
    filename = get_support_data_filename('google-analogies/questions-words.txt')
    quads = read_google_analogies(filename)
    vocab = [
        standardized_uri('en', word)
        for word in wordfreq.top_n_list('en', 200000)
    ]
    wrap = VectorSpaceWrapper(frame=frame)
    vecs = np.vstack([wrap.get_vector(word) for word in vocab])
    tframe = pd.DataFrame(vecs, index=vocab)
    total = 0
    correct = 0
    seen_mistakes = set()
    for quad in quads:
        prompt = quad[:3]
        answer = quad[3]
        vector = analogy_func(frame, *prompt)
        similar = similar_to_vec(tframe, vector)
        result = None
        for match in similar.index:
            if match not in prompt:
                result = match
                break
        if result == answer:
            correct += 1
        else:
            if result not in seen_mistakes:
                print(
                    "%s : %s :: %s : [%s] (should be %s)"
                    % (quad[0], quad[1], quad[2], result, answer)
                    )
                seen_mistakes.add(result)
        total += 1
    low, high = proportion_confint(correct, total)
    return pd.Series([correct / total, low, high], index=['acc', 'low', 'high'])
