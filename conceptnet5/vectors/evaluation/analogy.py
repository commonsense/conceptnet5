from collections import defaultdict
from itertools import groupby, product

import numpy as np
import pandas as pd
from scipy.stats import hmean, spearmanr
from statsmodels.stats.proportion import proportion_confint

import wordfreq
from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import standardized_uri
from conceptnet5.vectors.evaluation.wordsim import (
    confidence_interval,
    empty_comparison_table,
)
from conceptnet5.vectors.query import VectorSpaceWrapper


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
                    concept_pairs = [
                        tuple(standardized_uri('en', term) for term in pair)
                        for pair in raw_pairs
                    ]

                    # The first of the pairs we got is the prompt pair. The others are
                    # answers (a) through (e).
                    questions.append(
                        (concept_pairs[0], concept_pairs[1:], answer_index)
                    )
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
                pair = tuple(pair)
                train_pairs.append(pair)
    return train_pairs


def read_turk_answers_semeval2012(subset, subclass, test_questions):
    """
    A line represents one turker's answer to a given question. An answer has the
    following format:
    pair1, pair2, pair3, pair4, least_prototypical_pair, most_prototypical_pair, relation_name

    This function returns two dictionaries:
      * pairqnum2least -
      * pairqnum2most
    """
    filename = 'semeval12-2/{}/Phase2Answers-{}.txt'.format(subset, subclass)
    with open(get_support_data_filename(filename)) as file:
        answers = []
        for i, line in enumerate(file):
            if i == 0:
                continue
            pairs = tuple(line.split('\t'))
            answers.append(pairs)

        pairqnum2least = defaultdict(int)
        pairqnum2most = defaultdict(int)

        for question, answers in groupby(answers, key=lambda x: x[:4]):
            question_num = test_questions.index(question)
            for answer in answers:
                pairqnum2least[(question_num, answer[4])] += 1
                pairqnum2most[(question_num, answer[5])] += 1
        return pairqnum2least, pairqnum2most


def read_test_questions_semeval2012(subset, subclass):
    """
    Read test questions for a specific subclass. A test question has the following format:
    pair1,pair2,pair3,pair4
    """
    filename = 'semeval12-2/{}/Phase2Questions-{}.txt'.format(subset, subclass)
    with open(get_support_data_filename(filename)) as file:
        test_questions = []
        for line in file:
            pairs = tuple(line.strip().split(','))
            test_questions.append(pairs)
        return test_questions


def read_turk_ranks_semeval2012(subset, subclass):
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
            gold_ranks.append((pair, gold_score))
        return sorted(gold_ranks)


def read_bats(category):
    """
    Read BATS dataset pairs for a specific category. Turn them into questions.

    For some questions, BATS contains multiple answers. For example, the answer to an
    analogy question Nicaragua:Spanish::Switzerland:? could be German, French, or Italian. These
    will all be supplied as a list if they are an answer (b2). However, if they are a part of a
    question (b1), only the first one will be used.
    """
    filename = 'bats/{}.txt'.format(category)
    pairs = []
    with open(get_support_data_filename(filename)) as file:
        for line in file:
            if '\t' in line:
                left, right = line.lower().split('\t')
            else:
                left, right = line.lower().split()
            right = right.strip()
            if '/' in right:
                right = [i.strip() for i in right.split('/')]
            else:
                right = [i.strip() for i in right.split(',')]
            pairs.append([left, right])

    quads = []
    for i in range(len(pairs)):
        first_pair = pairs[i]
        first_pair[1] = first_pair[1][
            0
        ]  # select only one term for b1, even if more may be available
        second_pairs = [pair for j, pair in enumerate(pairs) if j != i]
        for second_pair in second_pairs:
            quad = []

            # the first three elements of a quad are the two terms in first_pair and the first
            # term of the second_pair
            quad.extend(
                [standardized_uri('en', term) for term in first_pair + second_pair[:1]]
            )

            # if the second element of the second pair (b2) is a list, it means there are multiple
            # correct answers for b2. We want to keep all of them.
            if isinstance(second_pair[1], list):
                quad.append([standardized_uri('en', term) for term in second_pair[1]])
            else:
                quad.append(standardized_uri('en', second_pair[1]))
            quads.append(quad)
    return quads


def analogy_func(wrap, a1, b1, a2, weight_direct=2 / 3, weight_transpose=1 / 3):
    """
    Find the vector representing the best b2 to complete the analogy
    a1 : b1 :: a2 : b2, according to `pairwise_analogy_func`.

    This is the partial derivative of `pairwise_analogy_func` with respect
    to b2.
    """
    va1 = wrap.get_vector(a1)
    vb1 = wrap.get_vector(b1)
    va2 = wrap.get_vector(a2)

    return (vb1 - va1) * weight_direct + (va2 - va1) * weight_transpose + vb1


def best_analogy_3cosmul(wrap, subframe, a1, b1, a2):
    """
    Find the best b2 to complete the analogy a1 : b1 :: a2 : b2, according
    to the 3CosMul metric.
    """
    va1 = wrap.get_vector(a1)
    vb1 = wrap.get_vector(b1)
    va2 = wrap.get_vector(a2)

    sa1 = subframe.dot(va1)
    sb1 = subframe.dot(vb1)
    sa2 = subframe.dot(va2)

    eps = 1e-6
    mul3cos = (sb1 + 1 + eps) * (sa2 + 1 + eps) / (sa1 + 1 + eps)

    best = mul3cos.dropna().nlargest(4)
    prompt = (a1, b1, a2)
    for term in best.index:
        if term not in prompt:
            return term


def pairwise_analogy_func(wrap, a1, b1, a2, b2, weight_direct, weight_transpose):
    """
    Rate the quality of the analogy a1 : b1 :: a2 : b2.
    """
    va1 = wrap.get_vector(a1)
    vb1 = wrap.get_vector(b1)
    va2 = wrap.get_vector(a2)
    vb2 = wrap.get_vector(b2)

    value = (
        weight_direct * (vb2 - va2).dot(vb1 - va1)
        + weight_transpose * (vb2 - vb1).dot(va2 - va1)
        + vb2.dot(vb1)
        + va2.dot(va1)
    )
    return value


def eval_pairwise_analogies(
    vectors, eval_filename, weight_direct, weight_transpose, subset='all'
):
    total = 0
    correct = 0
    for idx, (prompt, choices, answer) in enumerate(
        read_turney_analogies(eval_filename)
    ):
        # Enable an artificial training/test split
        if subset == 'all' or (subset == 'dev') == (idx % 2 == 0):
            a1, b1 = prompt
            choice_values = []
            for choice in choices:
                a2, b2 = choice
                choice_values.append(
                    pairwise_analogy_func(
                        vectors, a1, b1, a2, b2, weight_direct, weight_transpose
                    )
                )
            our_answer = np.argmax(choice_values)
            if our_answer == answer:
                correct += 1
            total += 1
    low, high = proportion_confint(correct, total)
    return pd.Series([correct / total, low, high], index=['acc', 'low', 'high'])


def optimize_weights(func, *args):
    """
    Both eval_pairwise_analogies() and eval_semeval2012_analogies() have three
    weights that can be tuned (and therefore two free parameters, as the total
    weight does not matter):

    - The *direct weight*, comparing (b2 - a2) to (b1 - a1)
    - The *transpose weight*, comparing (b2 - b1) to (a2 - a1)
    - The *similarity weight*, comparing b2 to b1 and a2 to a1

    This function takes a function for which to optimize the weights as an
    argument and returns the optimal weights, `weight_direct` and
    `weight_transpose`.
    """
    print('Tuning analogy weights')
    weights = [
        0.,
        0.05,
        0.1,
        0.15,
        0.2,
        0.3,
        0.35,
        0.4,
        0.5,
        0.6,
        0.65,
        0.7,
        0.8,
        0.9,
        1.0,
        1.5,
        2.0,
        2.5,
        3.0,
    ]
    best_weights = None
    best_acc = 0.
    for weight_direct in weights:
        for weight_transpose in weights:
            scores = func(
                *args,
                weight_direct=weight_direct,
                weight_transpose=weight_transpose,
                subset='dev'
            )
            if isinstance(scores, list):
                # If a function to optimize returns two results, like eval_semeval2012_analogies(),
                #  take their harmonic mean to compute the weights optimal for both results
                acc = hmean([scores[0].loc['acc'], scores[1].loc['acc']])
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


def eval_google_analogies(vectors, subset='semantic', vocab_size=200000, verbose=False):
    """
    Evaluate the Google Research analogies, released by Mikolov et al. along
    with word2vec.

    These analogies come in two flavors: semantic and syntactic. Numberbatch
    is intended to be a semantic space, so we focus on semantic analogies.

    The syntactic analogies are about whether you can inflect or conjugate a
    particular word. The semantic analogies are about whether you can sort
    words by their gender, and about geographic trivia.

    I (Rob) think this data set is not very representative, but evaluating
    against it is all the rage.
    """
    filename = get_support_data_filename('google-analogies/{}-words.txt'.format(subset))
    quads = read_google_analogies(filename)
    return eval_open_vocab_analogies(vectors, quads, vocab_size, verbose)


def eval_open_vocab_analogies(vectors, quads, vocab_size=200000, verbose=False):
    """
    Solve open vocabulary analogies, using 3CosMul function. This is used by Google and Bats
    test sets.
    """
    vocab = choose_vocab(quads, vocab_size)
    vecs = np.vstack([vectors.get_vector(word) for word in vocab])
    tframe = pd.DataFrame(vecs, index=vocab)
    total = 0
    correct = 0
    seen_mistakes = set()
    for quad in quads:
        prompt = quad[:3]
        answer = quad[3]
        result = best_analogy_3cosmul(vectors, tframe, *prompt)
        is_correct = (isinstance(answer, list) and result in answer) or (
            result == answer
        )
        if is_correct:
            correct += 1
        else:
            if verbose and result not in seen_mistakes:
                print(
                    "%s : %s :: %s : [%s] (should be %s)"
                    % (quad[0], quad[1], quad[2], result, answer)
                )
                seen_mistakes.add(result)
        total += 1
    low, high = proportion_confint(correct, total)
    result = pd.Series([correct / total, low, high], index=['acc', 'low', 'high'])
    if verbose:
        print(result)
    return result


def choose_vocab(quads, vocab_size):
    """
    Google and Bats analogies are not multiple-choice; instead, you're supposed to pick
    the best match out of your vector space's entire vocabulary, excluding the
    three words used in the prompt. The vocabulary size can matter a lot: Set
    it too high and you'll get low-frequency words that the data set wasn't
    looking for as answers. Set it too low and the correct answers won't be
    in the vocabulary.

    Set vocab_size='cheat' to see the results for an unrealistically optimal
    vocabulary (the vocabulary of the set of answer words).
    """
    if vocab_size == 'cheat':
        vocab = [
            standardized_uri('en', word)
            for word in sorted(set([quad[3] for quad in quads]))
        ]
    else:
        vocab = [
            standardized_uri('en', word)
            for word in wordfreq.top_n_list('en', vocab_size)
        ]
    return vocab


def eval_semeval2012_analogies(
    vectors, weight_direct, weight_transpose, subset, subclass
):
    """
    For a set of test pairs:
        * Compute a Spearman correlation coefficient between the ranks produced by vectors and
           gold ranks.
        * Compute an accuracy score of answering MaxDiff questions.
    """
    train_pairs = read_train_pairs_semeval2012(subset, subclass)
    test_questions = read_test_questions_semeval2012(subset, subclass)
    pairqnum2least, pairqnum2most = read_turk_answers_semeval2012(
        subset, subclass, test_questions
    )
    turk_rank = read_turk_ranks_semeval2012(subset, subclass)
    pairs_to_rank = [pair for pair, score in turk_rank]

    # Assign a score to each pair, according to pairwise_analogy_func
    our_pair_scores = {}
    for pair in pairs_to_rank:
        rank_pair_scores = []
        for train_pair in train_pairs:
            pair_to_rank = pair.strip().replace('"', '').split(':')
            score = pairwise_analogy_func(
                vectors,
                standardized_uri('en', train_pair[0]),
                standardized_uri('en', train_pair[1]),
                standardized_uri('en', pair_to_rank[0]),
                standardized_uri('en', pair_to_rank[1]),
                weight_direct,
                weight_transpose,
            )
            rank_pair_scores.append(score)
        our_pair_scores[pair] = np.mean(rank_pair_scores)

    # Answer MaxDiff questions using the ranks from the previous step
    correct_most = 0
    correct_least = 0
    total = 0

    for i, question in enumerate(test_questions):
        question_pairs_scores = []

        for question_pair in question:
            score = our_pair_scores[question_pair]
            question_pairs_scores.append(score)

        our_answer_most = question[np.argmax(question_pairs_scores)]
        our_answer_least = question[np.argmin(question_pairs_scores)]

        votes_guess_least = pairqnum2least[(i, our_answer_least)]
        votes_guess_most = pairqnum2most[(i, our_answer_most)]

        max_votes_least = 0
        max_votes_most = 0
        for question_pair in question:
            num_votes_least = pairqnum2least[(i, question_pair)]
            num_votes_most = pairqnum2most[(i, question_pair)]
            if num_votes_least > max_votes_least:
                max_votes_least = num_votes_least
            if num_votes_most > max_votes_most:
                max_votes_most = num_votes_most

        # a guess is correct if it got the same number of votes as the most frequent turkers' answer
        if votes_guess_least == max_votes_least:
            correct_least += 1
        if votes_guess_most == max_votes_most:
            correct_most += 1
        total += 1

    # Compute Spearman correlation of our ranks and MT ranks
    our_semeval_scores = [score for pair, score in sorted(our_pair_scores.items())]
    turk_semeval_scores = [score for pair, score in turk_rank]
    spearman = spearmanr(our_semeval_scores, turk_semeval_scores)[0]
    spearman_results = confidence_interval(spearman, total)

    # Compute an accuracy score on MaxDiff questions
    maxdiff = (correct_least + correct_most) / (2 * total)
    low_maxdiff, high_maxdiff = proportion_confint(
        (correct_least + correct_most), (2 * total)
    )
    maxdiff_results = pd.Series(
        [maxdiff, low_maxdiff, high_maxdiff], index=['acc', 'low', 'high']
    )

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
            maxdiff, spearman = eval_semeval2012_analogies(
                vectors, weight_direct, weight_transpose, subset, subclass
            )
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

    return [
        pd.Series(maxdiff_output, index=['acc', 'low', 'high']),
        pd.Series(spearman_output, index=['acc', 'low', 'high']),
    ]


def eval_bats_category(vectors, category, vocab_size=200000, verbose=False):
    """
    Evaluate a single category of BATS dataset.
    """
    quads = read_bats(category)
    category_results = eval_open_vocab_analogies(vectors, quads, vocab_size, verbose)
    return category_results


def evaluate(
    frame,
    analogy_filename,
    subset='test',
    tune_analogies=True,
    scope='global',
    google_vocab_size=200000,
):
    """
    Run SAT and Semeval12-2 evaluations.

    Required parameters:
      frame
          a DataFrame containing term vectors
      analogy_filename
          the filename of Turney's SAT evaluation data

    Optional parameters:
      subset (string, default 'test')
          a subset of a data to evaluate on, either 'test' or 'dev'
      tune_analogies (boolean, default True)
          tune the weights in eval_pairwise_analogies()
      semeval_scope (string, default 'global')
          'global' to get the average of the results across all subclasses of semeval12-2,
          or another string to get the results broken down by a subclass (1a, 1b, etc.)
    """
    vectors = VectorSpaceWrapper(frame=frame)
    results = empty_comparison_table()

    if tune_analogies:
        sat_weights = optimize_weights(
            eval_pairwise_analogies, vectors, analogy_filename
        )
        semeval_weights = optimize_weights(eval_semeval2012_global, vectors)
    else:
        sat_weights = (0.35, 0.65)
        semeval_weights = (0.3, 0.35)

    sat_results = eval_pairwise_analogies(
        vectors, analogy_filename, sat_weights[0], sat_weights[1], subset
    )
    results.loc['sat-analogies'] = sat_results

    for gsubset in ['semantic', 'syntactic']:
        google_results = eval_google_analogies(
            vectors, subset=gsubset, vocab_size=google_vocab_size
        )
        results.loc['google-%s' % gsubset] = google_results

    # There's no meaningful "all" subset for semeval12, because the dev and
    # test data are stored entirely separately. Just use "test".
    if subset == 'dev':
        semeval12_subset = 'dev'
    else:
        semeval12_subset = 'test'
    if scope == 'global':
        maxdiff_score, spearman_score = eval_semeval2012_global(
            vectors, semeval_weights[0], semeval_weights[1], semeval12_subset
        )
        results.loc['semeval12-spearman'] = spearman_score
        results.loc['semeval12-maxdiff'] = maxdiff_score
    else:
        for subclass in product(range(1, 11), 'a b c d e f g h i j'):
            subclass = ''.join([str(element) for element in subclass])
            try:
                maxdiff_score, spearman_score = eval_semeval2012_analogies(
                    vectors,
                    semeval_weights[0],
                    semeval_weights[1],
                    semeval12_subset,
                    subclass,
                )
                results.loc['semeval12-{}-spearman'.format(subclass)] = spearman_score
                results.loc['semeval12-{}-maxdiff'.format(subclass)] = maxdiff_score
            except FileNotFoundError:
                continue

    bats_results = []
    for category in product('DEIL', range(1, 11)):
        category = ''.join([str(element) for element in category])
        quads = read_bats(category)
        category_results = eval_open_vocab_analogies(vectors, quads)
        bats_results.append((category, category_results))

    if scope == 'global':
        average_scores = []
        for interval in ['acc', 'low', 'high']:
            average_scores.append(
                np.mean([result[interval] for name, result in bats_results])
            )
        results.loc['bats'] = pd.Series(average_scores, index=['acc', 'low', 'high'])
    else:
        for name, result in bats_results:
            results.loc['bats-{}'.format(''.join(name))] = result

    return results
