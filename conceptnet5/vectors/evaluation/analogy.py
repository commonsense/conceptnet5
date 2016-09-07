from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import standardized_uri, get_vector, similar_to_vec
from conceptnet5.vectors.query import VectorSpaceWrapper
import wordfreq
import numpy as np


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


def pairwise_analogy_func(frame, a1, b1, a2, b2):
    va1 = get_vector(frame, a1)
    vb1 = get_vector(frame, b1)
    va2 = get_vector(frame, a2)
    vb2 = get_vector(frame, b2)

    # (b2 - a2) * (b1 - a1) = (b1b2 - a1b2 - b1a2 + a1a2)
    # (b2 - b1) * (a2 - a1) = (a2b2 - a1b2 - b1a2 + a1b1)
    #
    # Positive contributors: a1a2, b1b2, a1b1, a2b2
    # Negative contributors: a1b2, b1a2
    # Irrelevant: a1b1
    return va1.dot(va2) + vb1.dot(vb2) + va1.dot(vb1) + va2.dot(vb2) - va1.dot(vb2) - vb1.dot(va2)


def eval_pairwise_analogies(frame, eval_filename):
    total = 0
    correct = 0
    for prompt, choices, answer in read_turney_analogies(eval_filename):
        a1, b1 = prompt
        choice_values = []
        for choice in choices:
            a2, b2 = choice
            choice_values.append(pairwise_analogy_func(frame, a1, b1, a2, b2))
        our_answer = np.argmax(choice_values)
        if our_answer == answer:
            correct += 1
        total += 1
    return correct, total, correct / total



def eval_analogies(frame):
    filename = get_support_data_filename('google-analogies/questions-words.txt')
    quads = read_google_analogies(filename)
    vocab = [
        standardized_uri('en', word)
        for word in wordfreq.top_n_list('en', 100000)
    ]
    tframe = frame.loc[vocab]
    total = 0
    correct = 0
    for quad in quads:
        if all(term in tframe.index for term in quad):
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
                print(
                    "%s : %s :: %s : %s (should be %s)"
                    % (quad[0], quad[1], quad[2], result.upper(), answer)
                    )
            total += 1
    return correct, total, correct / total
