from itertools import combinations

import numpy as np
import pandas as pd
from scipy.stats import hmean, pearsonr, spearmanr, tmean

from conceptnet5.util import get_support_data_filename
from conceptnet5.vectors import cosine_similarity, get_vector, standardized_uri
from conceptnet5.vectors.query import VectorSpaceWrapper

SAMPLE_SIZES = {
    'ws353': 353,
    'ws353-es': 353,
    'ws353-ro': 353,
    'men3000': 3000,
    'mturk': 771,
    'rw': 2034,
    'gur350-de': 350,
    'zg222-de': 222,
    'simlex': 999,
    'scws': 2003,
    'pku500-zh': 500,
    'jsim-ja': 4429,
    'semeval-2a-en': 500,
    'semeval-2a-de': 500,
    'semeval-2a-es': 500,
    'semeval-2a-it': 500,
    'semeval-2a-fa': 500,
    'semeval17-2a': 2000,
    'semeval-2b-de-es': 956,
    'semeval-2b-de-fa': 888,
    'semeval-2b-de-it': 912,
    'semeval-2b-en-de': 914,
    'semeval-2b-en-es': 978,
    'semeval-2b-en-fa': 952,
    'semeval-2b-en-it': 970,
    'semeval-2b-es-fa': 914,
    'semeval-2b-es-it': 967,
    'semeval-2b-it-fa': 916,
    'semeval17-2b': 5697,
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
    'Oxford': 'Botha and Blunsom (2014)',
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
    return pd.Series([rho, np.tanh(low), np.tanh(high)], index=['acc', 'low', 'high'])


def empty_comparison_table():
    return pd.DataFrame(columns=['acc', 'low', 'high'])


def make_comparison_table(scores):
    evals = sorted(scores)
    table = pd.DataFrame(index=evals, columns=['acc', 'low', 'high'])
    for evalname, score in scores.items():
        table.loc[evalname] = confidence_interval(score, SAMPLE_SIZES[evalname])
    return table


COMPARISONS = {}

# Here are all the existing evaluation results we know about, classified by
# what institution produced the results and which method is implemented.

# TODO: Update COMPARISONS and fill in the Semeval results once the group affiliations become
# available

# Levy et al., 2015
COMPARISONS['Bar-Ilan', 'PPMI'] = make_comparison_table(
    {
        'men3000': .745,
        'mturk': .686,
        'rw': .462,
        'simlex': .393,
        'ws353': .721,  # estimate
    }
)

COMPARISONS['Bar-Ilan', 'SVD'] = make_comparison_table(
    {
        'men3000': .778,
        'mturk': .666,
        'rw': .514,
        'simlex': .432,
        'ws353': .733,  # estimate
    }
)

COMPARISONS['Bar-Ilan', 'SGNS'] = make_comparison_table(
    {
        'men3000': .774,
        'mturk': .693,
        'rw': .470,
        'simlex': .438,
        'ws353': .729,  # estimate
    }
)

COMPARISONS['Bar-Ilan', 'GloVe'] = make_comparison_table(
    {
        'men3000': .729,
        'mturk': .632,
        'rw': .403,
        'simlex': .398,
        'ws353': .654,  # estimate
    }
)

COMPARISONS['Google', 'word2vec SGNS'] = make_comparison_table(
    {'men3000': .732, 'rw': .385, 'ws353': .624, 'scws': .574}
)

# Speer and Chin, 2016 - arXiv:1604.01692v1
COMPARISONS['Luminoso', 'GloVe'] = make_comparison_table(
    {'rw': .528, 'men3000': .840, 'ws353': .798}
)

COMPARISONS['Luminoso', 'word2vec SGNS'] = make_comparison_table(
    {'rw': .476, 'men3000': .778, 'ws353': .731}
)

COMPARISONS['Luminoso', 'Numberbatch 2016.04'] = make_comparison_table(
    {'rw': .596, 'men3000': .859, 'ws353': .821}
)

COMPARISONS['Luminoso', 'PPMI'] = make_comparison_table(
    {'rw': .420, 'men3000': .764, 'ws353': .651, 'scws': .608}
)

# Pennington et al., 2014
COMPARISONS['Stanford', 'GloVe'] = make_comparison_table(
    {'rw': .477, 'men3000': .816, 'ws353': .759}
)

# Joulin et al., 2016 - "Bag of Tricks"
# Rounded-off numbers from the blog post at https://research.facebook.com/blog/fasttext/
COMPARISONS['Facebook', 'fastText'] = make_comparison_table(
    {'rw': .46, 'ws353': .73, 'gur350-de': .69, 'zg222-de': .37}
)

# Salle et al., 2016 - LexVec
# https://github.com/alexandres/lexvec
COMPARISONS['UFRGS', 'LexVec'] = make_comparison_table(
    {
        'rw': .489,
        'simlex': .384,
        'scws': .652,
        'ws353': .661,
        'men3000': .759,
        'mturk': .655,
    }
)

COMPARISONS['Google+HL', 'SG+Morph'] = make_comparison_table(
    {'rw': .418, 'ws353': .712, 'gur350-de': .641, 'zg222-de': .215, 'ws353-es': .473}
)

COMPARISONS['Oxford', 'BB2014'] = make_comparison_table(
    {'rw': .300, 'ws353': .400, 'gur350-de': .560, 'zg222-de': .250}
)

# Comparisons from SemEval results
COMPARISONS['SemEval2017', 'Luminoso'] = make_comparison_table(
    {
        'semeval-2a-en': .789,
        'semeval-2a-de': .700,
        'semeval-2a-es': .743,
        'semeval-2a-it': .741,
        'semeval-2a-fa': .503,
        'semeval-2b-en-de': .763,
        'semeval-2b-en-es': .761,
        'semeval-2b-en-it': .776,
        'semeval-2b-en-fa': .598,
        'semeval-2b-de-es': .728,
        'semeval-2b-de-it': .741,
        'semeval-2b-de-fa': .598,
        'semeval-2b-es-it': .753,
        'semeval-2b-es-fa': .627,
        'semeval-2b-it-fa': .604,
    }
)

COMPARISONS['SemEval2017', 'Nasari'] = make_comparison_table(
    {
        # This is the baseline system, by Uniroma
        'semeval-2a-en': .682,
        'semeval-2a-de': .514,
        'semeval-2a-es': .600,
        'semeval-2a-it': .596,
        'semeval-2a-fa': .405,
        'semeval-2b-en-de': .598,
        'semeval-2b-en-es': .633,
        'semeval-2b-en-it': .648,
        'semeval-2b-en-fa': .505,
        'semeval-2b-de-es': .549,
        'semeval-2b-de-it': .561,
        'semeval-2b-de-fa': .458,
        'semeval-2b-es-it': .595,
        'semeval-2b-es-fa': .479,
        'semeval-2b-it-fa': .486,
    }
)

COMPARISONS['SemEval2017', 'QLUT'] = make_comparison_table({'semeval-2a-en': .778})

COMPARISONS['SemEval2017', 'HCCL'] = make_comparison_table(
    {
        'semeval-2a-en': .687,
        'semeval-2a-de': .594,
        'semeval-2a-es': .701,
        'semeval-2a-it': .651,
        'semeval-2a-fa': .436,
        'semeval-2b-en-de': .307,
        'semeval-2b-en-es': .087,
        'semeval-2b-en-it': .055,
        'semeval-2b-en-fa': .012,
        'semeval-2b-de-es': .045,
        'semeval-2b-de-it': .037,
        'semeval-2b-de-fa': .023,
        'semeval-2b-es-it': .064,
        'semeval-2b-es-fa': .048,
        'semeval-2b-it-fa': .000,
    }
)

COMPARISONS['SemEval2017', 'Mahtab'] = make_comparison_table({'semeval-2a-fa': .715})

COMPARISONS['SemEval2017', 'hhu'] = make_comparison_table(
    {'semeval-2a-en': .704, 'semeval-2a-fa': .604, 'semeval-2b-en-fa': .513}
)

COMPARISONS['SemEval2017', 'OoO'] = make_comparison_table(
    {
        'semeval-2b-en-de': .570,
        'semeval-2b-en-es': .584,
        'semeval-2b-en-it': .584,
        'semeval-2b-de-es': .549,
        'semeval-2b-de-it': .548,
        'semeval-2b-es-it': .570,
    }
)

COMPARISONS['SemEval2017', 'SEW'] = make_comparison_table(
    {
        'semeval-2a-en': .464,
        'semeval-2a-de': .449,
        'semeval-2a-es': .616,
        'semeval-2a-it': .569,
        'semeval-2a-fa': .393,
        'semeval-2b-en-de': .464,
        'semeval-2b-en-es': .505,
        'semeval-2b-en-it': .526,
        'semeval-2b-en-fa': .420,
        'semeval-2b-de-es': .530,
        'semeval-2b-de-it': .520,
        'semeval-2b-de-fa': .428,
        'semeval-2b-es-it': .595,
        'semeval-2b-es-fa': .515,
        'semeval-2b-it-fa': .489,
    }
)

COMPARISONS['SemEval2017', 'RUFINO'] = make_comparison_table(
    {
        'semeval-2a-en': .656,
        'semeval-2a-de': .539,
        'semeval-2a-es': .549,
        'semeval-2a-it': .476,
        'semeval-2a-fa': .360,
        'semeval-2b-en-de': .330,
        'semeval-2b-en-es': .340,
        'semeval-2b-en-it': .342,
        'semeval-2b-en-fa': .373,
        'semeval-2b-de-es': .318,
        'semeval-2b-de-it': .327,
        'semeval-2b-de-fa': .267,
        'semeval-2b-es-it': .356,
        'semeval-2b-es-fa': .300,
        'semeval-2b-it-fa': .249,
    }
)

COMPARISONS['SemEval2017', 'Citius'] = make_comparison_table(
    {'semeval-2a-en': .651, 'semeval-2a-es': .523, 'semeval-2b-en-es': .577}
)

COMPARISONS['SemEval2017', 'l2f'] = make_comparison_table({'semeval-2a-en': .649})

COMPARISONS['SemEval2017', 'gpv8'] = make_comparison_table(
    {'semeval-2a-en': .555, 'semeval-2a-de': .347, 'semeval-2a-it': .499}
)

COMPARISONS['SemEval2017', 'MERALI'] = make_comparison_table({'semeval-2a-en': .594})

COMPARISONS['SemEval2017', 'Amateur'] = make_comparison_table({'semeval-2a-en': .589})

COMPARISONS['SemEval2017', 'Wild Devs'] = make_comparison_table({'semeval-2a-en': .468})

# Hypothetical SemEval runs of existing systems
COMPARISONS['SemEval2017', 'fastText'] = make_comparison_table(
    {
        'semeval-2a-en': .468,
        'semeval-2a-de': .507,
        'semeval-2a-es': .417,
        'semeval-2a-it': .344,
        'semeval-2a-fa': .334,
    }
)

# Hypothetical SemEval runs of existing systems
COMPARISONS['SemEval2017', 'Luminoso, no OOV'] = make_comparison_table(
    {
        'semeval-2a-en': .747,
        'semeval-2a-de': .599,
        'semeval-2a-es': .611,
        'semeval-2a-it': .606,
        'semeval-2a-fa': .363,
        'semeval-2b-en-de': .696,
        'semeval-2b-en-es': .675,
        'semeval-2b-en-it': .677,
        'semeval-2b-en-fa': .502,
        'semeval-2b-de-es': .620,
        'semeval-2b-de-it': .612,
        'semeval-2b-de-fa': .501,
        'semeval-2b-es-it': .613,
        'semeval-2b-es-fa': .482,
        'semeval-2b-it-fa': .474,
    }
)

COMPARISONS['SemEval2017', 'word2vec'] = make_comparison_table({'semeval-2a-en': .575})


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


def read_simlex():
    lang1, lang2 = 'en', 'en'
    with open(get_support_data_filename('simlex/SimLex-999.txt')) as file:
        for line in file:
            if line.startswith("word1"):
                continue
            term1, term2, _, sscore, _, _, _, ascore, _, _ = line.split('\t')
            gold_score = float(sscore)
            yield term1, term2, gold_score, lang1, lang2


def read_pku500():
    lang1, lang2 = 'zh', 'zh'
    filename = 'pku-500/pku-500.csv'
    with open(get_support_data_filename(filename)) as file:
        for line in file:
            if line.startswith('#'):
                continue
            term1, term2, sscore = line.split('\t')
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
    filename = get_support_data_filename(
        'mensim/MEN_dataset_lemma_form.{}'.format(subset)
    )
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


def read_jsim():
    """
    Read the updated Japanese rare-words dataset from Karpinska et al.
    (http://www.aclweb.org/anthology/W18-2905)
    """
    lang1, lang2 = 'ja', 'ja'
    for pos in ('noun', 'verb', 'adj', 'adv'):
        filename = get_support_data_filename(
            'jSIM/similarity_full/score_{}_new_full.csv'.format(pos)
        )
        with open(filename, encoding='utf-8') as file:
            for line in file:
                if line.startswith('word1'):
                    continue
                parts = line.split(',')
                yield parts[0].strip(), parts[1].strip(), float(parts[2]), lang1, lang2


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
    filename = get_support_data_filename(
        'semeval17-2/{}-{}.{}.txt'.format(lang1, lang2, subset)
    )

    with open(filename) as file:
        for line in file:
            parts = line.split('\t')
            yield parts[0], parts[1], float(parts[2]), lang1, lang2


def compute_semeval_score(pearson_score, spearman_score):
    """
    Return NaN if a dataset can't be evaluated on a given frame. Return 0 if at least one similarity
    measure was 0 or negative. Otherwise, take a harmonic mean of a Pearson correlation coefficient
    and a Spearman correlation coefficient.
    """
    intervals = ['acc', 'low', 'high']
    scores = []
    for interval in intervals:
        if any(
            np.isnan(x) for x in [spearman_score[interval], pearson_score[interval]]
        ):
            scores.append(float('NaN'))
        elif any(x <= 0 for x in [spearman_score[interval], pearson_score[interval]]):
            scores.append(0)
        else:
            scores.append(hmean([spearman_score[interval], pearson_score[interval]]))

    return pd.Series(scores, index=intervals)


def evaluate_semeval_monolingual(vectors, lang):
    """
    Get a semeval score for a single monolingual test set.
    """
    spearman_score = measure_correlation(
        spearmanr, vectors, read_semeval_monolingual(lang)
    )
    pearson_score = measure_correlation(
        pearsonr, vectors, read_semeval_monolingual(lang)
    )
    score = compute_semeval_score(spearman_score, pearson_score)
    return score


def evaluate_semeval_crosslingual(vectors, lang1, lang2):
    """
    Get a semeval score for a single crosslingual test set
    """
    spearman_score = measure_correlation(
        spearmanr, vectors, read_semeval_crosslingual(lang1, lang2)
    )
    pearson_score = measure_correlation(
        pearsonr, vectors, read_semeval_crosslingual(lang1, lang2)
    )
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

    top_scores = sorted(
        scores, key=lambda x: x['acc'] if not np.isnan(x['acc']) else 0
    )[-4:]
    acc_average = tmean([score['acc'] for score in top_scores])
    low_average = tmean([score['low'] for score in top_scores])
    high_average = tmean([score['high'] for score in top_scores])
    return pd.Series(
        [acc_average, low_average, high_average], index=['acc', 'low', 'high']
    )


def evaluate_semeval_crosslingual_global(vectors):
    """
    According to Semeval2017-Subtask2 rules. the global score is the average of the individual
    scores on the six cross-lingual datasets on which the system performs best. If less than six
    scores are supplied, the global score is NaN.
    """
    scores = []
    languages = ['en', 'de', 'es', 'it', 'fa']
    for lang1, lang2 in combinations(languages, 2):
        score = evaluate_semeval_crosslingual(vectors, lang1, lang2)
        scores.append(score)

    top_scores = sorted(
        scores, key=lambda x: x['acc'] if not np.isnan(x['acc']) else 0
    )[-6:]
    acc_average = tmean([score['acc'] for score in top_scores])
    low_average = tmean([score['low'] for score in top_scores])
    high_average = tmean([score['high'] for score in top_scores])
    return pd.Series(
        [acc_average, low_average, high_average], index=['acc', 'low', 'high']
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

        if isinstance(vectors, VectorSpaceWrapper):
            uri1 = standardized_uri(lang1, term1)
            uri2 = standardized_uri(lang2, term2)
            our_score = vectors.get_similarity(uri1, uri2)

        else:
            our_score = cosine_similarity(
                get_vector(vectors, term1, lang1), get_vector(vectors, term2, lang2)
            )

        if verbose > 1:
            print('%s\t%s\t%3.3f\t%3.3f' % (term1, term2, gold_score, our_score))
        gold_scores.append(gold_score)
        our_scores.append(our_score)

    correlation = correlation_function(np.array(gold_scores), np.array(our_scores))[0]

    if verbose:
        print("Correlation: %s" % (correlation,))

    return confidence_interval(correlation, len(gold_scores))


def evaluate(frame, subset='dev', semeval_scope='global'):
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
    simlex_score = measure_correlation(spearmanr, vectors, read_simlex())
    gur350_score = measure_correlation(spearmanr, vectors, read_gurevych('350'))
    zg222_score = measure_correlation(spearmanr, vectors, read_gurevych('222'))
    ws_score = measure_correlation(spearmanr, vectors, read_ws353())
    ws_es_score = measure_correlation(spearmanr, vectors, read_ws353_multilingual('es'))
    ws_ro_score = measure_correlation(spearmanr, vectors, read_ws353_multilingual('ro'))
    pku500_score = measure_correlation(spearmanr, vectors, read_pku500())
    jsim_score = measure_correlation(spearmanr, vectors, read_jsim())

    results = empty_comparison_table()
    results.loc['men3000'] = men_score
    results.loc['rw'] = rw_score
    results.loc['mturk'] = mturk_score
    results.loc['simlex'] = simlex_score
    results.loc['gur350-de'] = gur350_score
    results.loc['zg222-de'] = zg222_score
    results.loc['ws353'] = ws_score
    results.loc['ws353-es'] = ws_es_score
    results.loc['ws353-ro'] = ws_ro_score
    results.loc['pku500-zh'] = pku500_score
    results.loc['jsim-ja'] = jsim_score

    if semeval_scope == 'global':
        results.loc['semeval17-2a'] = evaluate_semeval_monolingual_global(vectors)
        results.loc['semeval17-2b'] = evaluate_semeval_crosslingual_global(vectors)

    else:
        languages = ['en', 'de', 'es', 'it', 'fa']

        for lang in languages:
            results.loc['semeval-2a-{}'.format(lang)] = evaluate_semeval_monolingual(
                vectors, lang
            )

        for lang1, lang2 in combinations(languages, 2):
            results.loc[
                'semeval-2b-{}-{}'.format(lang1, lang2)
            ] = evaluate_semeval_crosslingual(vectors, lang1, lang2)

    return results


def evaluate_raw(frame, subset='dev', semeval_scope='global'):
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
    pku500_score = measure_correlation(spearmanr, frame, read_pku500())
    jsim_score = measure_correlation(spearmanr, frame, read_jsim())

    results = empty_comparison_table()
    results.loc['men3000'] = men_score
    results.loc['rw'] = rw_score
    results.loc['mturk'] = mturk_score
    results.loc['gur350-de'] = gur350_score
    results.loc['zg222-de'] = zg222_score
    results.loc['ws353'] = ws_score
    results.loc['ws353-es'] = ws_es_score
    results.loc['ws353-ro'] = ws_ro_score
    results.loc['pku500-zh'] = pku500_score
    results.loc['jsim-ja'] = jsim_score

    if semeval_scope == 'global':
        results.loc['semeval17-2a'] = evaluate_semeval_monolingual_global(frame)
        results.loc['semeval17-2b'] = evaluate_semeval_crosslingual_global(frame)

    else:
        languages = ['en', 'de', 'es', 'it', 'fa']

        for lang in languages:
            results.loc['semeval-2a-{}'.format(lang)] = evaluate_semeval_monolingual(
                frame, lang
            )

        for lang1, lang2 in combinations(languages, 2):
            results.loc[
                'semeval-2b-{}-{}'.format(lang1, lang2)
            ] = evaluate_semeval_crosslingual(frame, lang1, lang2)
    return results


def comparison_table():
    comparisons = dict(COMPARISONS)
    comparison_list = sorted(comparisons)
    big_frame = pd.concat(
        [comparisons[key] for key in comparison_list],
        keys=pd.MultiIndex.from_tuples(comparison_list),
    )

    return big_frame.dropna()


def results_in_context(results, name=('Luminoso', 'Numberbatch 17.02')):
    comparisons = dict(COMPARISONS)
    comparisons[name] = results
    comparison_list = sorted(comparisons)
    big_frame = pd.concat(
        [comparisons[key] for key in comparison_list],
        keys=pd.MultiIndex.from_tuples(comparison_list),
    )

    return big_frame.dropna()
