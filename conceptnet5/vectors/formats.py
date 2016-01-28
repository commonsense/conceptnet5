import pandas as pd


def load_glove(filename, nrows=500000):
    return pd.read_table(
        filename, sep=' ', index_col=0, quoting=3,
        keep_default_na=False, na_values=[],
        names=['term'] + list(range(300)),
        nrows=nrows
    )
