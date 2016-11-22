import pandas as pd
import numpy as np
from scipy import sparse
import gzip
import struct
import wordfreq
import itertools
from .transforms import l1_normalize_columns, l2_normalize_rows, standardize_row_labels
from ..vectors import standardized_uri, get_vector
from conceptnet5.languages import COMMON_LANGUAGES
from conceptnet5.nodes import get_uri_language


def load_hdf(filename):
    return pd.read_hdf(filename, 'mat', encoding='utf-8')


def save_hdf(table, filename):
    return table.to_hdf(filename, 'mat', encoding='utf-8')


def save_npy_and_labels(table, matrix_filename, vocab_filename):
    np.save(matrix_filename, table.values)
    save_index_as_labels(table.index, vocab_filename)


def export_conceptnet_to_hyperwords(table, matrix_filename, vocab_filename, nrows):
    vecs = []
    labels = []
    english_labels = [
        standardized_uri('en', item)
        for item in wordfreq.top_n_list('en', nrows * 2, 'large')
    ]
    count = 0
    for label in english_labels:
        if label in table.index:
            labels.append(label.split('/')[-1])
            vecs.append(get_vector(table, label))
            count += 1
            if count >= nrows:
                break
    np.save(matrix_filename, np.vstack(vecs))
    save_index_as_labels(labels, vocab_filename)


def export_plain_text(table, uri_file, file_base):
    from ..vectors.query import VectorSpaceWrapper

    def vec_to_text_line(label, vec):
        cells = [label] + ['%4.4f' % val for val in vec]
        return ' '.join(cells)

    uri_main_file = gzip.open(file_base + '_uris_main.txt.gz', 'wt')
    english_main_file = gzip.open(file_base + '_en_main.txt.gz', 'wt')
    english_extra_file = gzip.open(file_base + '_en_extra.txt.gz', 'wt')
    wrap = VectorSpaceWrapper(frame=table)

    for line in open(uri_file, encoding='utf-8'):
        uri = line.strip()
        if uri.count('/') == 3 and get_uri_language(uri) in COMMON_LANGUAGES:
            if uri in table.index:
                vec = table.loc[uri].values
                print(vec_to_text_line(uri, vec), file=uri_main_file)
            else:
                if not uri.startswith('/c/en') or '_' in uri:
                    continue
                vec = wrap.get_vector(uri)

            if vec.dot(vec) == 0:
                continue

            if uri.startswith('/c/en/'):
                label = uri[6:]
                if uri in table.index:
                    print(vec_to_text_line(label, vec), file=english_main_file)
                else:
                    print(vec_to_text_line(label, vec), file=english_extra_file)

    uri_main_file.close()
    english_main_file.close()
    english_extra_file.close()


def convert_glove(glove_filename, output_filename, nrows):
    """
    Convert GloVe data from a gzipped text file to an HDF5 dataframe.
    """
    glove_raw = load_glove(glove_filename, nrows)
    glove_std = standardize_row_labels(glove_raw, forms=False)
    del glove_raw
    glove_normal = l2_normalize_rows(l1_normalize_columns(glove_std))
    del glove_std
    save_hdf(glove_normal, output_filename)


def convert_fasttext(fasttext_filename, output_filename, nrows):
    """
    Convert FastText data from a gzipped text file to an HDF5 dataframe.
    """
    ft_raw = load_fasttext(fasttext_filename, nrows)
    ft_std = standardize_row_labels(ft_raw, forms=False)
    del ft_raw
    ft_normal = l2_normalize_rows(l1_normalize_columns(ft_std))
    del ft_std
    save_hdf(ft_normal, output_filename)


def convert_word2vec(word2vec_filename, output_filename, nrows, language='en'):
    """
    Convert word2vec data from its gzipped binary format to an HDF5
    dataframe.
    """
    w2v_raw = load_word2vec_bin(word2vec_filename, nrows)
    w2v_std = standardize_row_labels(w2v_raw, forms=False, language=language)
    del w2v_raw
    w2v_normal = l2_normalize_rows(l1_normalize_columns(w2v_std))
    del w2v_std
    save_hdf(w2v_normal, output_filename)


def load_glove(filename, nrows=500000):
    with gzip.open(filename, 'rt') as infile:
        return pd.read_table(
            infile, sep=' ', index_col=0, quoting=3,
            keep_default_na=False, na_values=[],
            names=['term'] + list(range(300)),
            nrows=nrows
        )


def load_fasttext(filename, nrows=1000000, ncols=300):
    arr = np.zeros((nrows, ncols))
    labels = []
    with gzip.open(filename, 'rt') as infile:
        for i, line in enumerate(itertools.islice(infile, 1, None)):
            if i >= nrows:
                break
            items = line.rstrip().split(' ')
            labels.append(items[0])
            values = [float(x) for x in items[1:]]
            arr[i] = values

    return pd.DataFrame(arr, index=labels)


def _read_until_space(file):
    chars = []
    while True:
        newchar = file.read(1)
        if newchar == b'' or newchar == b' ':
            break
        chars.append(newchar[0])
    return bytes(chars).decode('utf-8', 'replace')


def _read_vec(file, ndims):
    fmt = 'f' * ndims
    bytes_in = file.read(4 * ndims)
    values = list(struct.unpack(fmt, bytes_in))
    return np.array(values)


def load_word2vec_bin(filename, nrows):
    label_list = []
    vec_list = []
    with gzip.open(filename, 'rb') as infile:
        header = infile.readline().rstrip()
        nrows_str, ncols_str = header.split()
        nrows = min(int(nrows_str), nrows)
        ncols = int(ncols_str)
        for row in range(nrows):
            label = _read_until_space(infile)
            vec = _read_vec(infile, ncols)
            if label == '</s>':
                # Skip the word2vec sentence boundary marker, which will not
                # correspond to anything in other data
                continue
            label_list.append(label)
            vec_list.append(vec)
    mat = np.array(vec_list)
    return pd.DataFrame(mat, index=label_list, dtype='f')


def save_csr(matrix, filename):
    np.savez(filename, data=matrix.data, indices=matrix.indices,
             indptr=matrix.indptr, shape=matrix.shape)


def load_labels_and_npy(label_file, npy_file):
    labels = [line.rstrip('\n') for line in open(label_file, encoding='utf-8')]
    npy = np.load(npy_file)
    return pd.DataFrame(npy, index=labels, dtype='f')


def load_labels_as_index(label_filename):
    labels = [line.rstrip('\n') for line in open(label_filename, encoding='utf-8')]
    return pd.Index(labels)


def save_index_as_labels(index, label_filename):
    with open(label_filename, 'w', encoding='utf-8') as out:
        for label in index:
            print(label, file=out)


def load_csr(filename):
    with np.load(filename) as npz:
        mat = sparse.csr_matrix((npz['data'], npz['indices'], npz['indptr']), shape=npz['shape'])
    return mat
