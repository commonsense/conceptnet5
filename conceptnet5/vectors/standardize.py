from conceptnet5.nodes import standardized_concept_uri
import re


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


def standardized_uri(language, term):
    return replace_numbers(standardized_concept_uri(language, term))

