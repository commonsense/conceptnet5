from .formats import load_glove, save_hdf
from .transforms import l1_normalize_columns, standardize_row_labels


def convert_glove(glove_filename, output_filename, nrows):
    glove_raw = load_glove(glove_filename, nrows)
    glove_std = standardize_row_labels(glove_raw)
    del glove_raw
    glove_normal = l1_normalize_columns(glove_std)
    del glove_std
    save_hdf(glove_normal, output_filename)
