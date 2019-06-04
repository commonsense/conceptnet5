import numpy as np
import pandas as pd

import wordfreq
from conceptnet5.languages import CORE_LANGUAGES
from conceptnet5.uri import split_uri

from .debias import de_bias_frame
from .formats import load_hdf


def term_freq(term):
    """
    Get an estimate of the frequency of this term from the 'wordfreq' library.
    When miniaturizing, we use this as a cutoff for which words to include
    in the vocabulary.

    Because we have the most data for English, we allow lower word frequencies
    in English (by reading in the 'large' list, whose frequencies can go
    below 1e-6).
    """
    _c, lang, term = split_uri(term)[:3]
    if lang == 'en':
        return wordfreq.word_frequency(term, 'en', 'large')
    elif lang in CORE_LANGUAGES:
        return wordfreq.word_frequency(term, lang)
    else:
        return 0.


def miniaturize(input_filename, other_vocab=None, k=300, debias=True):
    """
    Produce a small matrix with good coverage of English and reasonable
    coverage of the other 'core languages' in ConceptNet. Three things that
    make the matrix smaller are:

    - Vocabulary pruning
    - Dimensionality reduction (if k < 300)
    - Quantization to 8-bit ints

    With `debias=True` (the default), this will run the de-biasing process
    after dimensionality reduction and before quantization. This is more
    effective than running it entirely before or after miniaturization.
    """
    # In practice, wordfreq doesn't even have single words with frequencies
    # below 1e-8, so this could just as well say 'term_freq(term) > 0'.
    # But this cutoff is clearer and adjustable.
    #
    # Non-English languages use terms with frequency 1e-6 or greater, because
    # only that much of the list has been loaded.
    frame_index = load_hdf(input_filename, index_only=True)
    vocab1 = [
        term for term in frame_index if '_' not in term and term_freq(term) >= 1e-8
    ]
    vocab_set = set(vocab1)
    if other_vocab is not None:
        extra_vocab = [
            term
            for term in other_vocab
            if '_' in term and term in frame_index and term not in vocab_set
        ]
        extra_vocab = extra_vocab[:20000]
    else:
        extra_vocab = []

    vocab = vocab1 + extra_vocab
    del vocab1, extra_vocab, vocab_set

    # Produce 'smaller', a version of the frame with only the selected vocabulary in
    # 'vocab'.
    #
    # We'd like to set smaller = load_hdf(input_filename).loc[vocab].values,
    # but that could run out of memory.  So we process the frame in shards.
    smaller = None
    n_rows = len(vocab)
    shard_size = int(250e6)  # about one (decimal) gigabyte of float32
    n_shards = (n_rows + shard_size - 1) // shard_size
    for i_shard in range(n_shards):
        shard_start = i_shard * shard_size
        shard_end = min(shard_start + shard_size, n_rows)
        shard = load_hdf(input_filename, start_row=shard_start, end_row=shard_end)
        if smaller is None:
            n_cols = shard.values.shape[1]
            smaller = np.empty(shape=(n_rows, n_cols), dtype=np.float32)
        smaller[shard_start:shard_end, :] = shard.loc[
            vocab[shard_start:shard_end]
        ].values

    # Take the SVD and keep only the top `k` components
    U, _S, _Vt = np.linalg.svd(smaller, full_matrices=False)
    del smaller, _S, _Vt
    redecomposed = pd.DataFrame(U[:, :k], index=vocab, dtype='f')
    del U, vocab

    # De-biasing is more effective after dimensionality reduction than before
    if debias:
        de_bias_frame(redecomposed)

    # Convert to 8-bit integers
    mini = (redecomposed * 64).astype(np.int8)
    mini.sort_index(inplace=True)
    return mini
