import sys
import pickle

from ftfy import fix_text

import numpy as np

from sklearn.preprocessing import normalize
from assoc_space import AssocSpace, LabelSet
from conceptnet5.nodes import standardized_concept_uri
from wordfreq import word_frequency

def conceptnet_standardize(text):
    """
    Normalizes a text into a concept URI. This function assume the text is
    english.
    """
    return standardized_concept_uri('en', text)

def load_glove_vectors(filename, labels, filter_beyond_row=250000,
                        end_row=1000000, frequency_cutoff=1e-6,
                        verbose=10000, standardize_text=True):
    """
    Loads glove vectors from a file and returns a list of numpy arrays.

    Each line of the file contains a word and a space separated vector. The
    lines are sorted by word frequency.

    This function will only parse at most `end_row` lines.

    If the index of a line is greater than `filter_beyond_row` and its
    frequency according to wordfreq is less than `frequency_cutoff`, it is
    ignored.
    """
    vectors = []
    with open(filename, encoding='latin-1') as file:
        for i, line in enumerate(file):
            if end_row is not None and i >= end_row:
                break
            if i % verbose == 0:
                print(i)

            parts = line.rstrip().split(' ')
            ctext = fix_text(parts[0]).replace('\n', '').strip()

            if standardize_text:
                try:
                    concept = conceptnet_standardize(ctext)
                except ValueError: # Bad concept names
                    continue

                if filter_beyond_row is not None and \
                    i >= filter_beyond_row and \
                    word_frequency(ctext, 'en') < frequency_cutoff:
                    continue

            else:
                concept = ctext

            index = labels.add(concept)

            #We extend `vectors` to the appropriate length
            while index >= len(vectors):
                vectors.append(np.zeros(len(parts)-1))

            # We need to combine words with the same normalization, but
            # different raw forms. We approximate this according to zipf's law
            if standardize_text:
                zipf_weight = 1 / (i + 1)
                vec = np.array([float(part) for part in parts[1:]])
                vectors[index] += vec * zipf_weight
            else:
                vectors[index] += vec

    return np.array(vectors)


def glove_to_assoc_space(filename, label_filename, glove_filename):
    labels = LabelSet()
    vectors = load_glove_vectors(filename, labels)
    pickle.dump(list(labels), open(label_filename, mode='wb'))
    np.save(glove_filename, vectors)

if __name__ == '__main__':
    glove_to_assoc_space(sys.argv[1], sys.argv[2], sys.argv[3])
