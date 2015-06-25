import sys

import numpy as np

from retrofit_glove import load_glove_vectors
from assoc_space import AssocSpace, LabelSet
from assoc_space.eigenmath import normalize_rows

def glove_to_assoc_space(filename, output_dir):
    labels = LabelSet()
    vectors = load_glove_vectors(filename, labels)

    assoc = AssocSpace(normalize_rows(np.array(vectors)),
                        np.ones(len(vectors[0])), labels)
    assoc.save_dir(output_dir)

if __name__ == '__main__':
    glove_to_assoc_space(sys.argv[1], sys.argv[2])
