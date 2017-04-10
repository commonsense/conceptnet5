import wordfreq
import numpy as np
import pandas as pd

from conceptnet5.uri import split_uri
from conceptnet5.languages import CORE_LANGUAGES
from .debias import de_bias_frame


def term_freq(term):
    _c, lang, term = split_uri(term)[:3]
    if lang == 'en':
        return wordfreq.word_frequency(term, 'en', 'large')
    elif lang in CORE_LANGUAGES:
        return wordfreq.word_frequency(term, lang)
    else:
        return 0.


def miniaturize(frame, prefix='/c/', other_vocab=None, k=300):
    """
    Produce a small matrix with good coverage of English and reasonable
    coverage of the other 'core languages' in ConceptNet. A `prefix` can be
    provided to limit the result to one language.
    """
    vocab1 = [term for term in frame.index if '_' not in term
              and term.startswith(prefix) and term_freq(term) > 0.]
    vocab_set = set(vocab1)
    if other_vocab is not None:
        extra_vocab = [term for term in other_vocab if '_' in term and
                       term in frame.index and term not in vocab_set]
        extra_vocab = extra_vocab[:20000]
    else:
        extra_vocab = []

    vocab = vocab1 + extra_vocab
    smaller = frame.loc[vocab]
    U, _S, _Vt = np.linalg.svd(smaller, full_matrices=False)
    redecomposed = pd.DataFrame(U[:, :k], index=vocab, dtype='f')
    redecomposed = de_bias_frame(redecomposed)
    mini = (redecomposed * 64).astype(np.int8)
    mini.sort_index(inplace=True)
    return mini
