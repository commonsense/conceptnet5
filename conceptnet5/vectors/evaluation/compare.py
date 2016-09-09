from conceptnet5.vectors.evaluation import analogy, story, wordsim
from conceptnet5.vectors.formats import load_hdf, load_glove, load_word2vec_bin
import numpy as np
import pandas as pd


# The filename of Turney's SAT evaluation data, which cannot be distributed
# with this code and must be requested from Peter Turney.
ANALOGY_FILENAME = '/hd/data/analogy/SAT-package-V3.txt'


def load_any_embeddings(filename):
    if filename.endswith('.bin.gz'):
        return load_word2vec_bin(filename, 1000000)
    elif filename.endswith('.gz'):
        return load_glove(filename, 1000000)
    elif filename.endswith('.h5'):
        return load_hdf(filename)
    else:
        raise ValueError("Can't recognize file extension of %r" % filename)


def compare_embeddings(filenames, subset='dev'):
    embeddings = [
        load_any_embeddings(filename) for filename in filenames
    ]
    results = []
    for frame in embeddings:
        wordsim_results = wordsim.evaluate(frame, subset=subset)
        analogy_results = analogy.eval_pairwise_analogies(
            frame, ANALOGY_FILENAME, subset=subset
        ).to_frame(name='sat-analogies').T
        story_results = story.evaluate(frame, subset=subset).to_frame('story-cloze').T
        results.append(
            pd.concat(
                [wordsim_results, analogy_results, story_results],
                axis=0
            )
        )
    return pd.concat(results, keys=filenames)
