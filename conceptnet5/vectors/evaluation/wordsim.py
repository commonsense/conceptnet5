from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import standardized_uri, get_vector, cosine_similarity
from conceptnet5.vectors.query import VectorSpaceWrapper
from scipy.stats import spearmanr, pearsonr, tmean, hmean
from itertools import combinations
import numpy as np
import pandas as pd

SAMPLE_SIZES = {
    'ws353': 353,
    'ws353-es': 353,
    'ws353-ro': 353,
    'men3000': 3000,
    'mturk': 771,
    'rw': 2034,
    'gur350-de': 350,
    'zg222-de': 222,
}

# A mapping from short group names to more formal citations
GROUPS = {
    'Luminoso': 'Speer and Chin (2016)',
    'Bar-Ilan': 'Levy et al. (2015)',
    'Google': 'Mikolov et al. (2013)',
    'Facebook': 'Joulin et al. (2016)',
    'Stanford': 'Pennington et al. (2014)',
    'UFRGS': 'Salle et al. (2016)',
    'Google+HL': 'Soricut and Och (2015)',
    'Oxford': 'Botha and Blunsom (2014)'
}


def confidence_interval(rho, N):
    """
    Give a 95% confidence interval for a Spearman correlation score, given
    the correlation and the number of cases.
    """
    z = np.arctanh(rho)
    interval = 1.96 / np.sqrt(N - 3)
    low = z - interval
    high = z + interval
    return pd.Series(
        [rho, np.tanh(low), np.tanh(high)],
        index=['acc', 'low', 'high']
    )


def empty_comparison_table():
    return pd.DataFrame(
        columns=['acc', 'low', 'high']
    )


def make_comparison_table(scores):
    table = empty_comparison_table()
    for evalname, score in scores.items():
        if evalname in table.index:
            table.loc[evalname] = confidence_interval(score, SAMPLE_SIZES[evalname])
    return table


COMPARISONS = {}

# Here are all the existing evaluation results we know about, classified by
# what institution produced the results and which method is implemented.

# TODO: Update COMPARISONS and fill in the Semeval results once the group affiliations become
# available

# Levy et al., 2015
COMPARISONS['Bar-Ilan', 'PPMI'] = make_comparison_table({
    'men3000': .745,
    'mturk': .686,
    'rw': .462,
    'simlex': .393,
    'ws353': .721  # estimate
})

COMPARISONS['Bar-Ilan', 'SVD'] = make_comparison_table({
    'men3000': .778,
    'mturk': .666,
    'rw': .514,
    'simlex': .432,
    'ws353': .733  # estimate
})

COMPARISONS['Bar-Ilan', 'SGNS'] = make_comparison_table({
    'men3000': .774,
    'mturk': .693,
    'rw': .470,
    'simlex': .438,
    'ws353': .729  # estimate
})

COMPARISONS['Bar-Ilan', 'GloVe'] = make_comparison_table({
    'men3000': .729,
    'mturk': .632,
    'rw': .403,
    'simlex': .398,
    'ws353': .654  # estimate
})

COMPARISONS['Google', 'word2vec SGNS'] = make_comparison_table({
    'men3000': .732,
    'rw': .385,
    'ws353': .624,
    'scws': .574
})

# Speer and Chin, 2016 - arXiv:1604.01692v1
COMPARISONS['Luminoso', 'GloVe'] = make_comparison_table({
    'rw': .528,
    'men3000': .840,
    'ws353': .798
})

COMPARISONS['Luminoso', 'word2vec SGNS'] = make_comparison_table({
    'rw': .476,
    'men3000': .778,
    'ws353': .731
})

COMPARISONS['Luminoso', 'Numberbatch 2016.04'] = make_comparison_table({
    'rw': .596,
    'men3000': .859,
    'ws353': .821
})

COMPARISONS['Luminoso', 'PPMI'] = make_comparison_table({
    'rw': .420,
    'men3000': .764,
    'ws353': .651,
    'scws': .608
})

# Pennington et al., 2014
COMPARISONS['Stanford', 'GloVe'] = make_comparison_table({
    'rw': .477,
    'men3000': .816,
    'ws353': .759
})

# Joulin et al., 2016 - "Bag of Tricks"
# Rounded-off numbers from the blog post at https://research.facebook.com/blog/fasttext/
COMPARISONS['Facebook', 'fastText'] = make_comparison_table({
    'rw': .46,
    'ws353': .73,
    'gur350-de': .69,
    'zg222-de': .37,
})

# Salle et al., 2016 - LexVec
# https://github.com/alexandres/lexvec
COMPARISONS['UFRGS', 'LexVec'] = make_comparison_table({
    'rw': .489,
    'simlex': .384,
    'scws': .652,
    'ws353': .661,
    'men3000': .759,
    'mturk': .655
})

COMPARISONS['Google+HL', 'SG+Morph'] = make_comparison_table({
    'rw': .418,
    'ws353': .712,
    'gur350-de': .641,
    'zg222-de': .215,
    'ws353-es': .473,
})

COMPARISONS['Oxford', 'BB2014'] = make_comparison_table({
    'rw': .300,
    'ws353': .400,
    'gur350-de': .560,
    'zg222-de': .250
})


def read_ws353():
    """
    Parses the word-similarity 353 test collection (ws353). ws353 is a
    collection of 353 english word pairs, each with a relatedness rating between
    0 (totally unrelated) to 10 (very related or identical). The relatedness
    of a pair of words was determined by the average scores of either 13
    or 16 native english speakers.
    """
    lang1, lang2 = 'en', 'en'
    with open(get_support_data_filename('wordsim-353/combined.csv')) as file:
        for line in file:
            if line.startswith('Word 1'):  # Skip the header
                continue
            term1, term2, sscore = line.split(',')
            gold_score = float(sscore)
            yield term1, term2, gold_score, lang1, lang2


def read_ws353_multilingual(language):
    lang1, lang2 = language, language
    if language == 'es':
        language = 'es.fixed'
    filename = 'wordsim-353/{}.tab'.format(language)
    with open(get_support_data_filename(filename)) as file:
        for line in file:
            term1, term2, sscore = line.split('\t')
            gold_score = float(sscore)
            yield term1, term2, gold_score, lang1, lang2


def read_gurevych(setname):
    # The 'setname' here is a number indicating the number of word pairs
    # in the set.
    lang1, lang2 = 'de', 'de'
    filename = 'gurevych/wortpaare{}.gold.pos.txt'.format(setname)
    with open(get_support_data_filename(filename)) as file:
        for line in file:
            if line.startswith('#'):
                continue
            term1, term2, sscore, _pos1, _pos2 = line.rstrip().split(':')
            gold_score = float(sscore)
            yield term1, term2, gold_score, lang1, lang2


def read_mturk():
    lang1, lang2 = 'en', 'en'
    with open(get_support_data_filename('mturk/MTURK-771.csv')) as file:
        for line in file:
            term1, term2, sscore = line.split(',')
            gold_score = float(sscore)
            yield term1, term2, gold_score, lang1, lang2


def read_men3000(subset='dev'):
    """
    Parses the MEN test collection. MEN is a collection of 3000 english word
    pairs, each with a relatedness rating between 0 and 50. The relatedness of
    a pair of words was determined by the number of times the pair was selected
    as more related compared to another randomly chosen pair.
    """
    lang1, lang2 = 'en', 'en'
    filename = get_support_data_filename('mensim/MEN_dataset_lemma_form.{}'.format(subset))
    with open(filename) as file:
        for line in file:
            parts = line.rstrip().split()
            term1 = parts[0].split('-')[0]  # remove part of speech
            term2 = parts[1].split('-')[0]
            gold_score = float(parts[2])
            yield term1, term2, gold_score, lang1, lang2


def read_rg65():
    """
    Parses the Rubenstein and Goodenough word similarity test collection.
    """
    lang1, lang2 = 'en', 'en'
    filename = get_support_data_filename('rg65/EN-RG-65.txt')
    with open(filename) as file:
        for line in file:
            parts = line.split()
            yield parts[0], parts[1], float(parts[2]), lang1, lang2


def read_rw(subset='dev'):
    """
    Parses the rare word similarity test collection.
    """
    lang1, lang2 = 'en', 'en'
    filename = get_support_data_filename('rw/rw-{}.csv'.format(subset))
    with open(filename) as file:
        for line in file:
            parts = line.split()
            yield parts[0], parts[1], float(parts[2]), lang1, lang2


def read_mc():
    """
    Parses the Miller and Charles word similarity test collection.
    """
    filename = get_support_data_filename('mc/EN-MC-30.txt')
    with open(filename) as file:
        for line in file:
            parts = line.split()
            yield parts[0], parts[1], float(parts[2])


def read_semeval_monolingual(lang, subset='test'):
    """
    Parses Semeval2017-Task2 monolingual word similarity (subtask 1) test collection.
    """
    lang1, lang2 = lang, lang
    filename = get_support_data_filename('semeval17-2/{}.{}.txt'.format(lang, subset))
    with open(filename) as file:
        for line in file:
            parts = line.split('\t')
            yield parts[0], parts[1], float(parts[2]), lang1, lang2


def read_semeval_crosslingual(lang1, lang2, subset='test'):
    """
    Parses Semeval2017-Task2 crosslingual word similarity (Subtask2) test collection.
    """
    filename = get_support_data_filename('semeval17-2/{}-{}.{}.txt'.format(lang1, lang2, subset))

    with open(filename) as file:
        for line in file:
            parts = line.split('\t')
            yield parts[0], parts[1], float(parts[2]), lang1, lang2


def compute_semeval_score(pearson_score, spearman_score):
    """
    Take a harmonic mean of a Pearson correlation coefficient and a Spearman correlation
    coefficient.
    """
    if any(np.isnan(x) for x in [spearman_score['acc'], pearson_score['acc']]):
        acc_harmonic_mean = float('NaN')
        low_harmonic_mean = float('NaN')
        high_harmonic_mean = float('NaN')
    else:
        acc_harmonic_mean = hmean([spearman_score['acc'], pearson_score['acc']])
        low_harmonic_mean = hmean([spearman_score['low'], pearson_score['low']])
        high_harmonic_mean = hmean([spearman_score['high'], pearson_score['high']])

    return pd.Series(
        [acc_harmonic_mean, low_harmonic_mean, high_harmonic_mean],
        index=['acc', 'low', 'high']
    )


def evaluate_semeval_monolingual(vectors, lang):
    """
    Get a semeval score for a single monolingual test set.
    """
    spearman_score = measure_correlation(spearmanr, vectors, read_semeval_monolingual(lang))
    pearson_score = measure_correlation(pearsonr, vectors, read_semeval_monolingual(lang))
    score = compute_semeval_score(spearman_score, pearson_score)
    return score


def evaluate_semeval_crosslingual(vectors, lang1, lang2):
    """
    Get a semeval score for a single crosslingual test set
    """
    spearman_score = measure_correlation(spearmanr, vectors, read_semeval_crosslingual(lang1, lang2))
    pearson_score = measure_correlation(pearsonr, vectors, read_semeval_crosslingual(lang1, lang2))
    score = compute_semeval_score(spearman_score, pearson_score)
    return score


def evaluate_semeval_monolingual_global(vectors):
    """
    According to Semeval2017-Subtask2 rules, the global score for a system is the average the final
    individual scores on the four languages on which the system performed best. If less than four
    scores are supplied, the global score is NaN.
    """
    scores = []
    for lang in ['en', 'de', 'es', 'it', 'fa']:
        score = evaluate_semeval_monolingual(vectors, lang)
        scores.append(score)

    top_scores = sorted(scores, key=lambda x: x['acc'] if not np.isnan(x['acc']) else 0)[-4:]
    acc_average = tmean([score['acc'] for score in top_scores])
    low_average = tmean([score['low'] for score in top_scores])
    high_average = tmean([score['high'] for score in top_scores])
    return pd.Series(
        [acc_average, low_average, high_average],
        index=['acc', 'low', 'high']
    )


def evaluate_semeval_crosslingual_global(vectors):
    """
    According to Semeval2017-Subtask2 rules. the global score is the average of the individual
    scores on the six cross-lingual datasets on which the system performs best. If less than six
    scores are supplied, the global score is NaN.
    """

    scores = []
    for pair in ['en-de', 'en-es', 'en-fa', 'en-it', 'de-es', 'de-fa', 'de-it', 'es-fa', 'es-it',
                 'it-fa']:
        lang1, lang2 = pair.split('-')
        score = evaluate_semeval_crosslingual(vectors, lang1, lang2)
        scores.append(score)

    top_scores = sorted(scores, key=lambda x: x['acc'] if not np.isnan(x['acc']) else 0)[-6:]
    acc_average = tmean([score['acc'] for score in top_scores])
    low_average = tmean([score['low'] for score in top_scores])
    high_average = tmean([score['high'] for score in top_scores])
    return pd.Series(
        [acc_average, low_average, high_average],
        index=['acc', 'low', 'high']
    )


def measure_correlation(correlation_function, vectors, standard, verbose=0):
    """
    Tests assoc_space's ability to recognize word correlation. This function
    computes the spearman correlation between assoc_space's reported word
    correlation and the expected word correlation according to 'standard'.
    """
    gold_scores = []
    our_scores = []

    for term1, term2, gold_score, lang1, lang2 in standard:
        uri1 = standardized_uri(lang1, term1)
        uri2 = standardized_uri(lang2, term2)
        if isinstance(vectors, VectorSpaceWrapper):
            our_score = vectors.get_similarity(uri1, uri2)
        else:
            our_score = cosine_similarity(get_vector(vectors, uri1), get_vector(vectors, uri2))
        if verbose > 1:
            print('%s\t%s\t%3.3f\t%3.3f' % (term1, term2, gold_score, our_score))
        gold_scores.append(gold_score)
        our_scores.append(our_score)

    correlation = correlation_function(np.array(gold_scores), np.array(our_scores))[0]

    if verbose:
        print("Correlation: %s" % (correlation,))

    return confidence_interval(correlation, len(gold_scores))


def evaluate(frame, subset='dev', semeval_scope='per_language'):
    """
    Evaluate a DataFrame containing term vectors on its ability to predict term
    relatedness, according to MEN-3000, RW, MTurk-771, WordSim-353, and Semeval2017-Task2. Use a
    VectorSpaceWrapper to fill missing vocabulary from ConceptNet.

    Return a Series containing these labeled results.
    """
    if subset == 'all':
        men_subset = 'test'
    else:
        men_subset = subset

    vectors = VectorSpaceWrapper(frame=frame)

    men_score = measure_correlation(spearmanr, vectors, read_men3000(men_subset))
    rw_score = measure_correlation(spearmanr, vectors, read_rw(subset))
    mturk_score = measure_correlation(spearmanr, vectors, read_mturk())
    gur350_score = measure_correlation(spearmanr, vectors, read_gurevych('350'))
    zg222_score = measure_correlation(spearmanr, vectors, read_gurevych('222'))
    ws_score = measure_correlation(spearmanr, vectors, read_ws353())
    ws_es_score = measure_correlation(spearmanr, vectors, read_ws353_multilingual('es'))
    ws_ro_score = measure_correlation(spearmanr, vectors, read_ws353_multilingual('ro'))

    results = empty_comparison_table()
    results.loc['men3000'] = men_score
    results.loc['rw'] = rw_score
    results.loc['mturk'] = mturk_score
    results.loc['gur350-de'] = gur350_score
    results.loc['zg222-de'] = zg222_score
    results.loc['ws353'] = ws_score
    results.loc['ws353-es'] = ws_es_score
    results.loc['ws353-ro'] = ws_ro_score

    if semeval_scope == 'global':
        results.loc['semeval17-2a'] = evaluate_semeval_monolingual_global(vectors)
        results.loc['semeval17-2b'] = evaluate_semeval_crosslingual_global(vectors)

    else:
        languages = ['en', 'de', 'es', 'it', 'fa']

        for lang in languages:
            results.loc['semeval-2a-{}'.format(lang)] = evaluate_semeval_monolingual(vectors, lang)

        for lang1, lang2 in combinations(languages, 2):
            results.loc['semeval-2b-{}-{}'.format(lang1, lang2)] = evaluate_semeval_crosslingual(
                vectors, lang1, lang2)

    return results


def evaluate_raw(frame, subset='dev', semeval_scope='per_language'):
    """
    Evaluate a DataFrame containing term vectors on its ability to predict term
    relatedness, according to MEN-3000, RW, MTurk-771, WordSim-353, and Semeval2017-Task2. Return
    a Series containing these labeled results.
    """
    frame = frame.astype(np.float32)

    men_score = measure_correlation(spearmanr, frame, read_men3000(subset))
    rw_score = measure_correlation(spearmanr, frame, read_rw(subset))
    mturk_score = measure_correlation(spearmanr, frame, read_mturk())
    gur350_score = measure_correlation(spearmanr, frame, read_gurevych('350'))
    zg222_score = measure_correlation(spearmanr, frame, read_gurevych('222'))
    ws_score = measure_correlation(spearmanr, frame, read_ws353())
    ws_es_score = measure_correlation(spearmanr, frame, read_ws353_multilingual('es'))
    ws_ro_score = measure_correlation(spearmanr, frame, read_ws353_multilingual('ro'))

    results = empty_comparison_table()
    results.loc['men3000'] = men_score
    results.loc['rw'] = rw_score
    results.loc['mturk'] = mturk_score
    results.loc['gur350-de'] = gur350_score
    results.loc['zg222-de'] = zg222_score
    results.loc['ws353'] = ws_score
    results.loc['ws353-es'] = ws_es_score
    results.loc['ws353-ro'] = ws_ro_score

    if semeval_scope == 'global':
        results.loc['semeval17-2a'] = evaluate_semeval_monolingual_global(frame)
        results.loc['semeval17-2b'] = evaluate_semeval_crosslingual_global(frame)

    else:
        languages = ['en', 'de', 'es', 'it', 'fa']

        for lang in languages:
            results.loc['semeval-2a-{}'.format(lang)] = evaluate_semeval_monolingual(frame, lang)

        for lang1, lang2 in combinations(languages, 2):
            results.loc['semeval-2b-{}-{}'.format(lang1, lang2)] = evaluate_semeval_crosslingual(
                frame, lang1, lang2)
    return results


def results_in_context(results, name=('Luminoso', 'Numberbatch 16.09')):
    comparisons = dict(COMPARISONS)
    comparisons[name] = results
    comparison_list = sorted(comparisons)
    big_frame = pd.concat([comparisons[key] for key in comparison_list],
                          keys=pd.MultiIndex.from_tuples(comparison_list))

    return big_frame.dropna()
