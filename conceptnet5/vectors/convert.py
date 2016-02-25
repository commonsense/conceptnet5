from .formats import load_glove, load_word2vec_bin, save_hdf
from .transforms import l1_normalize_columns, l2_normalize_rows, standardize_row_labels


def convert_glove(glove_filename, output_filename, nrows):
    glove_raw = load_glove(glove_filename, nrows)
    glove_std = standardize_row_labels(glove_raw)
    del glove_raw
    glove_normal = l2_normalize_rows(l1_normalize_columns(glove_std))
    del glove_std
    save_hdf(glove_normal, output_filename)


def convert_word2vec(word2vec_filename, output_filename, nrows):
    w2v_raw = load_word2vec_bin(word2vec_filename, nrows)
    w2v_std = standardize_row_labels(w2v_raw)
    del w2v_raw
    w2v_normal = l2_normalize_rows(l1_normalize_columns(w2v_std))
    del w2v_std
    save_hdf(w2v_normal, output_filename)

