from scipy import sparse
import pandas as pd
from ordered_set import OrderedSet
import re

class SparseMatrixBuilder:
    """
    SparseMatrixBuilder is a utility class that helps build a matrix of
    unknown shape.
    """

    def __init__(self):
        self.rowIndex = []
        self.colIndex = []
        self.values = []

    def __setitem__(self, key, val):
        row, col = key
        self.rowIndex.append(row)
        self.colIndex.append(col)
        self.values.append(val)

    def tocsr(self, shape, dtype=float):
        return sparse.coo_matrix((self.values, (self.rowIndex, self.colIndex)),
                                 shape=shape, dtype=dtype).tocsr()


# TODO: move somewhere more appropriate
DOUBLE_DIGIT_RE = re.compile(r'[0-9][0-9]')
DIGIT_RE = re.compile(r'[0-9]')


def replace_numbers(s):
    """
    Replace digits with # in any term where a sequence of two digits appears.

    This operation is applied to text that passes through word2vec, so we
    should match it.
    """
    if DOUBLE_DIGIT_RE.search(s): 
        return DIGIT_RE.sub('#', s)
    else:
        return s


def build_from_conceptnet_table(filename):
    """
    Read a file of tab-separated association data from ConceptNet, such as
    `data/assoc/reduced.csv`. Return a SciPy sparse matrix of the associations,
    and an OrderedSet of labels.
    """
    mat = SparseMatrixBuilder()

    # TODO: rebalance by dataset? Or maybe do that when building the
    # associations in the first place.
    
    labels = OrderedSet()

    with open(filename, encoding='utf-8') as infile:
        for line in infile:
            concept1, concept2, value_str, dataset, relation = line.strip().split('\t')

            index1 = labels.add(replace_numbers(concept1))
            index2 = labels.add(replace_numbers(concept2))
            value = float(value_str)
            mat[index1, index2] = value
            mat[index2, index1] = value

    shape = (len(labels), len(labels))
    return mat.to_csr(shape), labels


def table_to_multi_index(filename):
    """
    Read a file of tab-separated association data from ConceptNet, such as
    `data/assoc/reduced.csv`. Return the result as a Pandas data structure:
    in particular, a multi-indexed Series.
    """
    index_tuples = []
    values = []
    with open(str(filename), encoding='utf-8') as infile:
        for line in infile:
            concept1, concept2, value_str, dataset, relation = line.strip().split('\t')
            if not concept1.endswith('/neg') and not concept2.endswith('/neg') and concept1 != concept2:
                concept1 = replace_numbers(concept1)
                concept2 = replace_numbers(concept2)
                index_tuples.append((concept1, concept2))
                values.append(float(value_str))

    index = pd.MultiIndex.from_tuples(index_tuples, names=['start', 'end'])
    series = pd.Series(values, index=index)
    return series.sort_index()
