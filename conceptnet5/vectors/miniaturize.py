import numpy as np
import pandas as pd

import wordfreq
from conceptnet5.languages import CORE_LANGUAGES
from conceptnet5.uri import split_uri

from .debias import de_bias_frame


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


def miniaturize(frame, other_vocab=None, k=300, debias=True):
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
    vocab1 = [
        term for term in frame.index if '_' not in term and term_freq(term) >= 1e-8
    ]
    vocab_set = set(vocab1)
    if other_vocab is not None:
        extra_vocab = [
            term
            for term in other_vocab
            if '_' in term and term in frame.index and term not in vocab_set
        ]
        extra_vocab = extra_vocab[:20000]
    else:
        extra_vocab = []

    vocab = vocab1 + extra_vocab
    smaller = frame.loc[vocab]
    U, _S, _Vt = np.linalg.svd(smaller, full_matrices=False)
    del smaller, _S, _Vt, vocab1, extra_vocab, vocab_set
    redecomposed = pd.DataFrame(U[:, :k], index=vocab, dtype='f')
    del U, vocab
    if debias:
        de_bias_frame(redecomposed)
    mini = (redecomposed * 64).astype(np.int8)
    mini.sort_index(inplace=True)
    return mini
