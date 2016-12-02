from conceptnet5.vectors.evaluation import analogy, story, wordsim
from conceptnet5.vectors.formats import load_hdf, save_hdf, load_glove, load_word2vec_bin
import numpy as np
import pandas as pd

# The filename of Turney's SAT evaluation data, which cannot be distributed
# with this code and must be requested from Peter Turney.
ANALOGY_FILENAME = 'data/raw/analogy/SAT-package-V3.txt'


def load_any_embeddings(filename):
    if filename.endswith('.bin.gz'):
        return load_word2vec_bin(filename, 1000000)
    elif filename.endswith('.gz'):
        return load_glove(filename, 1000000)
    elif filename.endswith('.h5'):
        return load_hdf(filename)
    else:
        raise ValueError("Can't recognize file extension of %r" % filename)


def compare_embeddings(filenames, subset='dev', tune_analogies=True):
    embeddings = [
        load_any_embeddings(filename) for filename in filenames
    ]
    results = []
    for frame in embeddings:
        wordsim_results = wordsim.evaluate(frame, subset=subset)
        if tune_analogies:
            analogy_results = analogy.tune_pairwise_analogies(
                frame, ANALOGY_FILENAME, subset=subset
            ).to_frame(name='sat-analogies').T
        else:
            analogy_results = analogy.eval_pairwise_analogies(
                frame, ANALOGY_FILENAME, subset=subset
            ).to_frame(name='sat-analogies').T
        story_results = story.evaluate(frame, subset=subset).to_frame('story-cloze').T
        results.append(
            pd.concat(
                [wordsim_results, analogy_results, story_results], axis=0
            )
        )
    result = pd.concat(results, keys=filenames)
    save_hdf(result, '/tmp/numberbatch-comparison.h5')
    return result


def graph_comparison(table_filename, out_filename):
    import matplotlib.pyplot as plt
    result = load_hdf(table_filename)
    plt.style.use('bmh')
    plt.rcParams['xtick.labelsize'] = 'x-large'
    plt.rcParams['ytick.labelsize'] = 'x-large'

    patterns = [ "/", "\\" , "//" , "\\\\" , " " ]
    width = 0.15
    evals = ['men3000', 'rw', 'mturk', 'ws353', 'story-cloze', 'sat-analogies']
    eval_labels = ['MEN-3000', 'Rare Words', 'MTurk-771', 'WS353', 'Story Cloze', 'SAT analogies']
    colors = [props['color'] for props in plt.rcParams['axes.prop_cycle']]

    systems = [
        ('word2vec Google News', 'data/raw/vectors/GoogleNews-vectors-negative300.bin.gz'),
        ('GloVe 1.2 840B', 'data/raw/vectors/glove12.840B.300d.txt.gz'),
        ('LexVec: enWP + NewsCrawl', 'data/raw/vectors/lexvec.no-header.vectors.gz'),
        ('ConceptNet-PPMI', 'data/precomputed/vectors/conceptnet-55-ppmi.h5'),
        ('ConceptNet Numberbatch', 'data/precomputed/vectors/numberbatch.h5')
    ]
    ind = np.arange(len(evals))

    fig, ax = plt.subplots(figsize=(16, 8))
    for i, (sysname, syspath) in enumerate(systems):
        eval_table = result.xs(syspath, level=0).loc[evals]
        errs = [eval_table['high'] - eval_table['acc'], eval_table['acc'] - eval_table['low']]
        ax.bar(ind + i * width, eval_table['acc'], width, hatch=patterns[i], color=colors[i], yerr=errs, ecolor='k')

    ax.set_ylim(0.0, 1.0)
    ax.set_yticks(np.arange(0.0, 1.1, 0.1))
    ax.legend([name for (name, path) in systems], bbox_to_anchor=(1.02, 1), loc=2, borderaxespad=0.)
    ax.set_xticks(ind + width * len(systems) / 2)
    ax.set_xticklabels(eval_labels)
    ax.xaxis.grid(False)
    plt.ylabel('Evaluation score', fontsize='x-large')
    plt.savefig(out_filename, bbox_inches="tight", dpi=300)
