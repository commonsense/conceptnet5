import contextlib
import gzip
import pickle
import struct
import tables

import numpy as np
import pandas as pd

from ordered_set import OrderedSet

from .transforms import l1_normalize_columns, standardize_row_labels


def load_hdf(filename, index_only=False, start_row=0, end_row=None):
    """
    Load a semantic vector space from an HDF5 file.

    HDF5 is a complex format that can contain many instances of different kinds
    of data. We store files in one of two formats:  either the file contains a
    single group named "data", wich in turn contains two arrays named "index"
    and "vectors", or the file contains a single group named "mat" (under which
    various data is saved by pandas to_hdf).

    If the optional argument index_only (default False) is set to True only the
    index (vocabulary) of the file will be returned.

    Optional arguments start_row and end_row may be given, in which case only
    rows in the range from the given start to one before the given end will
    be returned; this enables processing a large file in "horizontal" shards.
    If not specified, the start row defaults to 0 and the end to one past the
    final row of the file.

    If any of these optional arguments are specified and the file is in "data"
    format, only the requested data will be read from disk (which can save
    significant memory).  Files in "mat" format must be read in their entirety
    (though they still support the optional arguments; after reading only the
    requested data is returned) but allow storage of column labels.
    """
    with contextlib.closing(tables.open_file(filename, mode="r")) as file:
        if hasattr(file.root, "data"):
            # Handle a new-style file.
            if end_row is None:
                end_row = file.root.data.vectors.nrows
            index = pd.Index(
                array.tobytes().decode("utf-8")
                for array in file.root.data.index.iterrows(
                    start=start_row, stop=end_row
                )
            )
            if index_only:
                return index
            else:
                vectors = file.root.data.vectors.read(
                    start=start_row, stop=end_row
                )
                frame = pd.DataFrame(index=index, data=vectors)
                return frame

    # Handle old-style files.
    frame = pd.read_hdf(filename, "mat", encoding="utf-8")
    if end_row is None:
        end_row = len(frame)
    if index_only:
        return frame.index[start_row:end_row]
    else:
        return frame.iloc[start_row:end_row]


def save_hdf(table, filename, format="data"):
    """
    Save a semantic vector space into an HDF5 file.  If the optional argument
    "format" has value "data", the space will be stored under a group named
    "data", in two arrays named "index" and "vectors".  This format allows
    reading a subset of the rows of the space if desired.  Otherwise the space
    will be stored (using to_hdf) under a group named "mat".  This format does
    not allow partial reads (more precisely, load_hdf can be called on such
    files to read a subset of the rows, but the entire file will be read into
    memory before the subset is returned) but permits column labels to be
    stored.
    """
    if format == "data":
        with contextlib.closing(tables.open_file(filename, mode="w")) as file:
            file.create_group("/", "data", "Index and vector data.")
            file.create_array(
                file.root.data, name="vectors", byteorder="little", obj=table.values
            )
            index = file.create_vlarray(
                file.root.data,
                name="index",
                byteorder="little",
                atom=tables.UInt8Atom(shape=()),
            )
            for term in table.index:
                index.append(np.frombuffer(term.encode("utf-8"), np.uint8))
    else:
        table.to_hdf(filename, "mat", mode="w", encoding="utf-8")


def save_labels(table, vocab_filename):
    save_index_as_labels(table.index, vocab_filename)


def save_npy(values, matrix_filename):
    """
    Save a semantic vector space in two files: a NumPy .npy file of the matrix,
    and a text file with one label per line. We use this for exporting the
    Luminoso background space.
    """
    np.save(matrix_filename, values)


def vec_to_text_line(label, vec):
    """
    Output a labeled vector as a line in a fastText-style text format.
    """
    cells = [label] + ["%4.4f" % val for val in vec]
    return " ".join(cells)


def export_text(frame, filename, filter_language=None):
    """
    Save a semantic vector space as a fastText-style text file.

    If `filter_language` is set, it will output only vectors in that language.
    """
    vectors = frame.values
    index = frame.index
    if filter_language is not None:
        start_idx = index.get_loc("/c/%s/#" % filter_language, method="bfill")
        try:
            end_idx = index.get_loc("/c/%s0" % filter_language, method="bfill")
        except KeyError:
            end_idx = frame.shape[0]
        frame = frame.iloc[start_idx:end_idx]
        vectors = frame.values
        index = frame.index

    with gzip.open(filename, "wt") as out:
        dims = "%s %s" % frame.shape
        print(dims, file=out)
        for i in range(frame.shape[0]):
            label = index[i]
            if filter_language is not None:
                label = label.split("/", 3)[-1]
            vec = vectors[i]
            print(vec_to_text_line(label, vec), file=out)


def convert_glove(glove_filename, output_filename, nrows, nshards=6):
    """
    Convert GloVe data from a gzipped text file to shards in HDF5 dataframes.
    """
    ncols = len(load_glove(glove_filename, max_rows=1).columns)
    shard_length = (ncols + nshards - 1) // nshards
    for i_shard in range(nshards):
        start_column = i_shard * shard_length
        end_column = min(start_column + shard_length, ncols)
        shard_filename = output_filename + ".shard{}".format(i_shard)
        glove_raw = load_glove(
            glove_filename, nrows, start_column=start_column, end_column=end_column
        )
        glove_std = standardize_row_labels(glove_raw, forms=False)
        del glove_raw
        glove_normal = l1_normalize_columns(glove_std)
        save_hdf(glove_normal, shard_filename)


def convert_fasttext(fasttext_filename, output_filename, nrows, language, nshards=6):
    """
    Convert FastText data from a gzipped text file to shards in HDF5 dataframes.
    """
    ncols = len(load_fasttext(fasttext_filename, max_rows=1).columns)
    shard_length = (ncols + nshards - 1) // nshards
    for i_shard in range(nshards):
        start_column = i_shard * shard_length
        end_column = min(start_column + shard_length, ncols)
        shard_filename = output_filename + ".shard{}".format(i_shard)
        ft_raw = load_fasttext(
            fasttext_filename, nrows, start_column=start_column, end_column=end_column
        )
        ft_std = standardize_row_labels(ft_raw, forms=False, language=language)
        del ft_raw
        ft_normal = l1_normalize_columns(ft_std)
        del ft_std
        save_hdf(ft_normal, shard_filename)


def convert_word2vec(
    word2vec_filename, output_filename, nrows, language="en", nshards=6
):
    """
    Convert word2vec data from its gzipped binary format to shards in HDF5
    dataframes.
    """
    ncols = len(load_word2vec_bin(word2vec_filename, nrows=1).columns)
    shard_length = (ncols + nshards - 1) // nshards
    for i_shard in range(nshards):
        start_column = i_shard * shard_length
        end_column = min(start_column + shard_length, ncols)
        shard_filename = output_filename + ".shard{}".format(i_shard)
        w2v_raw = load_word2vec_bin(
            word2vec_filename, nrows, start_column=start_column, end_column=end_column
        )
        w2v_std = standardize_row_labels(w2v_raw, forms=False, language=language)
        del w2v_raw
        w2v_normal = l1_normalize_columns(w2v_std)
        del w2v_std
        save_hdf(w2v_normal, shard_filename)


def convert_polyglot(polyglot_filename, output_filename, language):
    """
    Convert Polyglot data from its pickled format to an HDF5 dataframe.
    """
    pg_raw = load_polyglot(polyglot_filename)
    pg_std = standardize_row_labels(pg_raw, language, forms=False)
    del pg_raw
    save_hdf(pg_std, output_filename)


def load_glove(filename, max_rows=1000000, start_column=0, end_column=None):
    """
    Load a DataFrame from the GloVe text format, which is the same as the
    fastText format except it doesn't tell you up front how many rows and
    columns there are.
    """
    arr = None
    label_list = []
    with gzip.open(filename, "rt") as infile:
        for i, line in enumerate(infile):
            if i >= max_rows:
                break
            items = line.rstrip().split(" ")
            label_list.append(items[0])
            if arr is None:
                ncols = len(items) - 1
                if end_column is None:
                    end_column = ncols
                if not 0 <= start_column <= ncols:
                    raise ValueError(
                        "Invalid start column {} (out of {}).".format(
                            start_column, ncols
                        )
                    )
                if end_column - start_column > ncols:
                    end_column = ncols
                ncols = end_column - start_column
                arr = np.zeros((max_rows, ncols), "f")
            values = [float(x) for x in items[1:]]
            arr[i] = values[start_column:end_column]

    if len(label_list) < max_rows:
        arr = arr[: len(label_list)]
    return pd.DataFrame(
        arr, index=label_list, dtype="f", columns=list(range(start_column, end_column))
    )


def load_fasttext(filename, max_rows=1000000, start_column=0, end_column=None):
    """
    Load a DataFrame from the fastText text format.
    """
    arr = None
    label_list = []
    with gzip.open(filename, "rt") as infile:
        nrows_str, ncols_str = infile.readline().rstrip().split()

        nrows = min(int(nrows_str), max_rows)
        ncols = int(ncols_str)
        if end_column is None:
            end_column = ncols
        if not 0 <= start_column <= ncols:
            raise ValueError(
                "Invalid start column {} (out of {}).".format(start_column, ncols)
            )
        if end_column - start_column > ncols:
            end_column = ncols
        ncols = end_column - start_column
        arr = np.zeros((nrows, ncols), dtype="f")
        for line in infile:
            if len(label_list) >= nrows:
                break
            items = line.rstrip().split(" ")
            label = items[0]
            if label != "</s>":
                values = [float(x) for x in items[1:]]
                arr[len(label_list)] = values[start_column:end_column]
                label_list.append(label)

    if len(label_list) < max_rows:
        arr = arr[: len(label_list)]
    return pd.DataFrame(
        arr, index=label_list, dtype="f", columns=list(range(start_column, end_column))
    )


def _read_until_space(file):
    chars = []
    while True:
        newchar = file.read(1)
        if newchar == b"" or newchar == b" ":
            break
        chars.append(newchar[0])
    return bytes(chars).decode("utf-8", "replace")


def _read_vec(file, ndims):
    fmt = "f" * ndims
    bytes_in = file.read(4 * ndims)
    values = list(struct.unpack(fmt, bytes_in))
    return np.array(values)


def load_word2vec_bin(filename, nrows, start_column=0, end_column=None):
    """
    Load a DataFrame from word2vec's binary format. (word2vec's text format
    should be the same as fastText's, but it's less efficient to load the
    word2vec data that way.)
    """
    label_list = []
    arr = None
    with gzip.open(filename, "rb") as infile:
        header = infile.readline().rstrip()
        nrows_str, ncols_str = header.split()
        nrows = min(int(nrows_str), nrows)
        ncols = int(ncols_str)
        if end_column is None:
            end_column = ncols
        if not 0 <= start_column <= ncols:
            raise ValueError(
                "Invalid start column {} (out of {}).".format(start_column, ncols)
            )
        if end_column - start_column > ncols:
            end_column = ncols
        requested_ncols = end_column - start_column
        arr = np.zeros((nrows, requested_ncols), dtype="f")
        while len(label_list) < nrows:
            label = _read_until_space(infile)
            vec = _read_vec(infile, ncols)
            if label == "</s>":
                # Skip the word2vec sentence boundary marker, which will not
                # correspond to anything in other data
                continue
            idx = len(label_list)
            arr[idx] = vec[start_column:end_column]
            label_list.append(label)

    return pd.DataFrame(
        arr, index=label_list, dtype="f", columns=list(range(start_column, end_column))
    )


def load_polyglot(filename):
    """
    Load a pickled matrix from the Polyglot format.
    """
    labels, arr = pickle.load(open(filename, "rb"), encoding="bytes")
    label_list = list(labels)
    return pd.DataFrame(arr, index=label_list, dtype="f")


def load_labels_and_npy(label_file, npy_file):
    """
    Load a semantic vector space from two files: a NumPy .npy file of the matrix,
    and a text file with one label per line.
    """
    label_list = [line.rstrip("\n") for line in open(label_file, encoding="utf-8")]
    arr = np.load(npy_file)
    return pd.DataFrame(arr, index=label_list, dtype="f")


def load_labels_as_index(label_filename):
    """
    Load a set of labels (with no attached vectors) from a text file, and
    represent them in a pandas Index.
    """
    labels = [line.rstrip("\n") for line in open(label_filename, encoding="utf-8")]
    return pd.Index(labels)


def save_index_as_labels(index, label_filename):
    """
    Save a pandas Index as a text file of labels.
    """
    with open(label_filename, "w", encoding="utf-8") as out:
        for label in index:
            print(label, file=out)


def save_ordered_set(oset, filename):
    """
    Save an OrderedSet object as a text file of words.
    """
    with open(filename, "w", encoding="utf-8") as out:
        for word in oset:
            print(word, file=out)


def load_ordered_set(filename):
    """
    Load a set of words  from a text file, and
    represent them in an OrderedSet object.
    """
    oset = OrderedSet()
    for line in open(filename, encoding="utf-8"):
        oset.append(line.rstrip("\n"))
    return oset
