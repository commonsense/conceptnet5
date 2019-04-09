import numpy as np
import pandas as pd

from conceptnet5.vectors.evaluation import analogy, story, wordsim
from conceptnet5.vectors.formats import (
    load_fasttext,
    load_glove,
    load_hdf,
    load_word2vec_bin,
    save_hdf,
)

# The filename of Turney's SAT evaluation data, which cannot be distributed
# with this code and must be requested from Peter Turney.
ANALOGY_FILENAME = 'data/raw/analogy/SAT-package-V3.txt'


def load_any_embeddings(filename):
    if filename.endswith('.bin.gz'):
        return load_word2vec_bin(filename, 1000000)
    elif filename.endswith('.vectors.gz') or filename.endswith('.vec.gz'):
        return load_fasttext(filename, 1000000)
    elif filename.endswith('.txt.gz'):
        return load_glove(filename, 1000000)
    elif filename.endswith('.h5'):
        return load_hdf(filename)
    else:
        raise ValueError("Can't recognize file extension of %r" % filename)


def compare_embeddings(filenames, subset='dev', run_analogies=False):
    results = []
    for filename in filenames:
        print(filename)
        frame = load_any_embeddings(filename)
        wordsim_results = wordsim.evaluate(
            frame, subset=subset, semeval_scope='per-language'
        )
        story_results = story.evaluate(frame, subset=subset).to_frame('story-cloze').T
        frame_results = [wordsim_results, story_results]

        if run_analogies:
            analogy_results = analogy.evaluate(frame, ANALOGY_FILENAME, subset=subset)
            frame_results.append(analogy_results)

        results.append(pd.concat(frame_results, axis=0))
    result = pd.concat(results, keys=filenames)
    save_hdf(result, '/tmp/numberbatch-comparison.h5')
    return result


def graph_comparison(table_filename, out_filename):
    import matplotlib.pyplot as plt

    result = load_hdf(table_filename)
    # plt.style.use('bmh')
    plt.rcParams['xtick.labelsize'] = 'x-large'
    plt.rcParams['ytick.labelsize'] = 'x-large'

    evals = ['men3000', 'rw', 'mturk', 'ws353', 'semeval-2a-en']
    eval_labels = [
        'MEN-3000',
        'Rare Words',
        'MTurk-771',
        'WordSim-353',
        'SemEval 2017-2a',
    ]
    prop_cycle = list(plt.rcParams['axes.prop_cycle'])
    colors = [props['color'] for props in prop_cycle]

    systems = [
        (
            'word2vec Google News',
            'data/raw/vectors/GoogleNews-vectors-negative300.bin.gz',
        ),
        ('GloVe 1.2 840B', 'data/raw/vectors/glove12.840B.300d.txt.gz'),
        ('GloVe renormalized', 'data/vectors/glove12-840B.h5'),
        ('fastText enWP (without OOV)', 'data/raw/vectors/fasttext-wiki-en.vec.gz'),
        # ('ConceptNet Numberbatch biased', 'data/vectors/numberbatch-biased.h5'),
        ('ConceptNet Numberbatch', 'data/vectors/numberbatch.h5'),
    ]
    width = 0.84 / len(systems)
    ind = np.arange(len(evals))

    fig, ax = plt.subplots(figsize=(16, 8))
    for i, (sysname, syspath) in enumerate(systems):
        eval_table = result.xs(syspath, level=0).loc[evals]
        value = eval_table['acc']
        errs = [eval_table['high'] - value, value - eval_table['low']]
        ax.bar(
            ind + i * width, value, width * 0.9, color=colors[i], yerr=errs, ecolor='k'
        )

    ax.set_ylim(0.0, 1.0)
    ax.set_yticks(np.arange(0.0, 1.1, 0.1))
    ax.legend(
        [name for (name, path) in systems],
        bbox_to_anchor=(1.02, 1),
        loc=2,
        borderaxespad=0.,
    )
    ax.set_xticks(ind + width * len(systems) / 2)
    ax.set_xticklabels(eval_labels)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    plt.ylabel(
        'Evaluation score (Spearman \N{GREEK SMALL LETTER RHO})', fontsize='x-large'
    )
    plt.savefig(out_filename, bbox_inches="tight", dpi=300)


def graph_bias_comparison(table_filename, out_filename):
    import matplotlib.pyplot as plt

    result = load_hdf(table_filename)
    # plt.style.use('bmh')
    plt.rcParams['xtick.labelsize'] = 'x-large'
    plt.rcParams['ytick.labelsize'] = 'x-large'

    evals = [
        'gender',
        'beliefs',
        'ethnicity-coarse',
        'ethnicity-fine',
        'ethnicity-names',
    ]
    eval_labels = [
        'Gender bias',
        'Religious bias',
        'Ethnic bias (coarse)',
        'Ethnic bias (fine)',
        'Bias from names',
    ]
    prop_cycle = list(plt.rcParams['axes.prop_cycle'])
    colors = [props['color'] for props in prop_cycle]

    systems = [
        (
            'word2vec Google News',
            'data/raw/vectors/GoogleNews-vectors-negative300.bin.gz',
        ),
        ('GloVe 1.2 840B', 'data/raw/vectors/glove12.840B.300d.txt.gz'),
        ('GloVe renormalized', 'data/vectors/glove12-840B.h5'),
        ('fastText enWP (without OOV)', 'data/raw/vectors/fasttext-wiki-en.vec.gz'),
        # ('ConceptNet Numberbatch biased', 'data/vectors/numberbatch-biased.h5'),
        ('ConceptNet Numberbatch 17.04', 'data/vectors/numberbatch.h5'),
    ]
    width = 0.84 / len(systems)
    ind = np.arange(len(evals))

    fig, ax = plt.subplots(figsize=(16, 8))
    for i, (sysname, syspath) in enumerate(systems):
        eval_table = result.xs(syspath, level=0).loc[evals]
        value = eval_table['bias']
        errs = [eval_table['high'] - value, value - eval_table['low']]
        ax.bar(
            ind + i * width, value, width * 0.9, color=colors[i], yerr=errs, ecolor='k'
        )

    ax.set_ylim(0.0, 0.4)
    ax.set_yticks(np.arange(0.0, 0.5, 0.1))
    ax.legend(
        [name for (name, path) in systems],
        bbox_to_anchor=(1.02, 1),
        loc=2,
        borderaxespad=0.,
    )
    ax.set_xticks(ind + width * len(systems) / 2)
    ax.set_xticklabels(eval_labels)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    plt.ylabel('Correlation with stereotypes', fontsize='x-large')
    plt.savefig(out_filename, bbox_inches="tight", dpi=300)
