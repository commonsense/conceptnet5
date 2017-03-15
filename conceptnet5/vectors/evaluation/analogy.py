from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import standardized_uri, get_vector, similar_to_vec
from conceptnet5.vectors.query import VectorSpaceWrapper
from statsmodels.stats.proportion import proportion_confint
from itertools import product
from scipy.stats import spearmanr
from conceptnet5.vectors.evaluation.wordsim import empty_comparison_table, confidence_interval
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
                    concept_pairs = [tuple(standardized_uri('en', term) for term in pair) for pair
                                     in raw_pairs]

                    # The first of the pairs we got is the prompt pair. The others are
                    # answers (a) through (e).
                    questions.append((concept_pairs[0], concept_pairs[1:], answer_index))
                    question_lines.clear()
                else:
                    question_lines.append(line)

    return questions


def read_train_pairs_semeval2012(subset, subclass):
    """
    Read a set of three training pairs for a given subclass. These pairs are
    used as prototypical examples of a given relation to which test pairs are compared.
    """
    filename = 'semeval12-2/{}/Phase1Questions-{}.txt'.format(subset, subclass)
    with open(get_support_data_filename(filename)) as file:
        train_pairs = []
        for i, line in enumerate(file):
            if i in [4, 5, 6]:
                pair = line.strip().split(':')
                pair = tuple(standardized_uri('en', term) for term in pair)
                train_pairs.append(pair)
    return train_pairs


def read_questions_semeval2012(subset, subclass):
    """
    Semeval2012 questions have the following format:
    pair1, pair2, pair3, pair4, least_prototypical_pair, most_prototypical_pair, relation_name
    """
    filename = 'semeval12-2/{}/Phase2Answers-{}.txt'.format(subset, subclass)
    with open(get_support_data_filename(filename)) as file:
        questions = []
        for i, line in enumerate(file):
            if i == 0:
                continue
            pairs = line.split('\t')
            pairs = [pair.split(':') for pair in pairs[:-1]]  # Skip relation label
            pairs = [tuple(standardized_uri('en', term) for term in pair) for pair in pairs]
            questions.append(pairs)
        return questions


def read_turk_ranks(subset, subclass):
    """
    Read gold rankings of prototypicality, as computed using turkers answers to MaxDiff
    questions.
    
    A score is defined as the difference between the number of times the turkers judged
    a pair the most prototypical and the number of times they judged it as the least
    prototypical. 
    """
    filename = 'semeval12-2/{}/GoldRatings-{}.txt'.format(subset, subclass)
    with open(get_support_data_filename(filename)) as file:
        gold_ranks = []
        for line in file:
            if line.startswith('#'):
                continue
            gold_score, pair = line.split()
            gold_score = float(gold_score)
            pair = pair.strip().replace('"', '').split(':')
            pair = tuple(standardized_uri('en', term) for term in pair)
            gold_ranks.append((pair, gold_score))
        return sorted(gold_ranks)


def analogy_func(frame, a1, b1, a2):
    return get_vector(frame, b1) - get_vector(frame, a1) + get_vector(frame, a2)


def pairwise_analogy_func(wrap, a1, b1, a2, b2, weight_direct, weight_transpose):
    va1 = wrap.get_vector(a1)
    vb1 = wrap.get_vector(b1)
    va2 = wrap.get_vector(a2)
    vb2 = wrap.get_vector(b2)

    value = (
        weight_direct * (vb2 - va2).dot(vb1 - va1)
        + weight_transpose * (vb2 - vb1).dot(va2 - va1)
        + vb2.dot(vb1) + va2.dot(va1)
    )
    return value


def eval_pairwise_analogies(vectors, eval_filename,
                            weight_direct, weight_transpose, subset='all'):
    total = 0
    correct = 0
    # wrap = VectorSpaceWrapper(vectors=vectors)
    for idx, (prompt, choices, answer) in enumerate(read_turney_analogies(eval_filename)):
        # Enable an artificial training/test split
        if subset == 'all' or (subset == 'dev') == (idx % 2 == 0):
            a1, b1 = prompt
            choice_values = []
            for choice in choices:
                a2, b2 = choice
                choice_values.append(
                    pairwise_analogy_func(vectors, a1, b1, a2, b2, weight_direct, weight_transpose)
                )
            our_answer = np.argmax(choice_values)
            if our_answer == answer:
                correct += 1
            total += 1
    low, high = proportion_confint(correct, total)
    return pd.Series([correct / total, low, high], index=['acc', 'low', 'high'])


def tune_pairwise_analogies(func, *args):
    """
    Our pairwise analogy function has three weights that can be tuned
    (and therefore two free parameters, as the total weight does not matter):

    - The *direct weight*, comparing (b2 - a2) to (b1 - a1)
    - The *transpose weight*, comparing (b2 - b1) to (a2 - a1)
    - The *similarity weight*, comparing b2 to b1 and a2 to a1

    """
    # Original search was more coarse-grained
    # weights = [
    #     0.25, 0.3, 0.4, 0.5, 0.6, 0.8,
    #     1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0
    # ]
    print('Tuning analogy weights')
    weights = [
        0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55,
        0.6, 0.65, 0.7, 0.75, 0.8, 0.9, 1.0
    ]
    best_weights = None
    best_acc = 0.
    for weight_direct in weights:
        for weight_transpose in weights:
            scores = func(*args, weight_direct, weight_transpose, subset='dev')
            if isinstance(scores, list):
                acc = scores[0].loc['acc']
            else:
                acc = scores.loc['acc']
            if acc > best_acc:
                print(weight_direct, weight_transpose, acc)
                best_weights = (weight_direct, weight_transpose)
                best_acc = acc
            elif acc == best_acc:
                print(weight_direct, weight_transpose, acc)
    weight_direct, weight_transpose = best_weights
    print()
    return weight_direct, weight_transpose


def eval_google_analogies(frame):
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


def eval_semeval2012_analogies(vectors, weight_direct, weight_transpose, subset, subclass):
    """
    For a test file:
        * Compute a Spearman correlation coefficient between the ranks produced by vectors and
           gold ranks.
        * Compute an accuracy score of answering MaxDiff questions.
    """
    train_pairs = read_train_pairs_semeval2012(subset, subclass)
    questions = read_questions_semeval2012(subset, subclass)
    turk_rank = read_turk_ranks(subset, subclass)
    pairs_to_rank = [pair for pair, score in turk_rank]

    # Assign a score to each pair, according to pairwise_analogy_func
    our_pair_scores = {}
    for pair in pairs_to_rank:
        rank_pair_scores = []
        for train_pair in train_pairs:
            score = pairwise_analogy_func(vectors, train_pair[0], pair[0],
                                          train_pair[1], pair[1], weight_direct, weight_transpose)
            rank_pair_scores.append(score)
        our_pair_scores[pair] = np.mean(rank_pair_scores)

    # Answer MaxDiff questions using the ranks from the previous step
    correct_most = 0
    correct_least = 0
    total = 0

    for i, question in enumerate(questions):
        question_pairs = question[:4]
        least = question[4]
        most = question[5]
        question_pairs_scores = []

        for question_pair in question_pairs:
            score = our_pair_scores[question_pair]
            question_pairs_scores.append(score)

        our_answer_most = question_pairs[np.argmax(question_pairs_scores)]
        our_answer_least = question_pairs[np.argmin(question_pairs_scores)]

        if most == our_answer_most:
            correct_most += 1
        if least == our_answer_least:
            correct_least += 1
        total += 1

    # Compute Spearman correlation of our ranks and MT ranks
    our_semeval_scores = [score for pair, score in sorted(our_pair_scores.items())]
    turk_semeval_scores = [score for pair, score in turk_rank]
    spearman = round(spearmanr(our_semeval_scores, turk_semeval_scores)[0], 3)
    spearman_results = confidence_interval(spearman, total)

    # Compute an accuracy score on MaxDiff questions
    maxdiff = round((correct_least + correct_most) / (total + total), 3)
    low_maxdiff, high_maxdiff = proportion_confint((correct_least + correct_most), (2 * total))
    maxdiff_results = pd.Series([maxdiff, low_maxdiff, high_maxdiff], index=['acc', 'low', 'high'])

    return [maxdiff_results, spearman_results]


def eval_semeval2012_global(vectors, weight_direct, weight_transpose, subset):
    """
    Return the average Spearman score and MaxDiff accuracy score for the entire test set.
    """
    spearman_scores = []
    maxdiff_scores = []
    for subclass in product(range(1, 11), 'a b c d e f g h i j'):
        subclass = ''.join([str(element) for element in subclass])
        try:
            maxdiff, spearman = eval_semeval2012_analogies(vectors, weight_direct,
                                                           weight_transpose,
                                                           subset, subclass)
            spearman_scores.append(spearman)
            maxdiff_scores.append(maxdiff)
        except FileNotFoundError:
            continue

    spearman_output = []
    maxdiff_output = []
    for interval in ['acc', 'low', 'high']:
        average_maxdiff_score = np.mean([score[interval] for score in maxdiff_scores])
        average_spearman_score = np.mean([score[interval] for score in spearman_scores])
        spearman_output.append(average_spearman_score)
        maxdiff_output.append(average_maxdiff_score)

    return [pd.Series(maxdiff_output, index=['acc', 'low', 'high']),
            pd.Series(spearman_output, index=['acc', 'low', 'high'])]


def evaluate(frame, analogy_filename, subset='test', tune_analogies=True, semeval_scope='global'):
    """
    Run SAT and Semeval12-2 evaluations.
    """
    vectors = VectorSpaceWrapper(frame=frame)
    results = empty_comparison_table()

    if tune_analogies:
        sat_weights = tune_pairwise_analogies(eval_pairwise_analogies, vectors, analogy_filename)
        semeval_weights = tune_pairwise_analogies(eval_semeval2012_global, vectors)
    else:
        sat_weights = (0.35, 0.65)
        semeval_weights = (0.2, 1.0)

    sat_results = eval_pairwise_analogies(vectors,
                                          analogy_filename,
                                          sat_weights[0],
                                          sat_weights[1],
                                          subset)
    results.loc['sat-analogies'] = sat_results

    if semeval_scope == 'global':
        maxdiff_score, spearman_score = eval_semeval2012_global(vectors,
                                                                semeval_weights[0],
                                                                semeval_weights[1],
                                                                subset)
        results.loc['semeval12-spearman'] = spearman_score
        results.loc['semeval12-maxdiff'] = maxdiff_score

    else:
        for subclass in product(range(1, 11), 'a b c d e f g h i j'):
            subclass = ''.join([str(element) for element in subclass])
            subclass = ''.join(subclass)
            try:
                maxdiff_score, spearman_score = eval_semeval2012_analogies(vectors,
                                                                           semeval_weights[0],
                                                                           semeval_weights[1],
                                                                           subset,
                                                                           subclass)
                results.loc['semeval12-{}-spearman'.format(subclass)] = spearman_score
                results.loc['semeval12-{}-maxdiff'.format(subclass)] = maxdiff_score
            except FileNotFoundError:
                continue

    return results
