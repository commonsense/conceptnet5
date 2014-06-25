from __future__ import with_statement, print_function, unicode_literals, division
from conceptnet5.util import get_support_data_filename


PHONETIC_DICT = {}
def _setup():
    """
    Read the dictionary file, creating a mapping from words to their
    phonetics.

    When multiple pronunciations are given, keep the last one.
    """
    with open(get_support_data_filename('cmudict.0.7a')) as rhymelist:
        for line in rhymelist:
            if line.startswith(';;;'): continue
            word, phon = line.strip().split('  ')
            phon = phon.split(' ')
            PHONETIC_DICT[word] = phon
_setup()


def get_phonetic(text):
    """
    Given a string which could contain multiple words, get the sequence of
    phonemes are the pronunciation of the sequence of words.

    When a pronunciation is not known, use the letters to stand for
    themselves.

    >>> get_phonetic('thing')
    ['TH', 'IH1', 'NG']
    >>> get_phonetic('thingummy')
    ['T', 'H', 'I', 'N', 'G', 'U', 'M', 'M', 'Y']
    >>> get_phonetic('concept net')
    ['K', 'AA1', 'N', 'S', 'EH0', 'P', 'T', 'N', 'EH1', 'T']
    """
    parts = []
    for word in text.split():
        parts.extend(PHONETIC_DICT.get(word.upper(), list(word.upper())))
    return parts


def edit_distance(list1, list2):
    """
    Find the minimum number of insertions, deletions, or replacements required
    to turn list1 into list2, using the typical dynamic programming algorithm.

    >>> edit_distance('test', 'test')
    0
    >>> edit_distance([], [])
    0
    >>> edit_distance('test', 'toast')
    2
    >>> edit_distance(['T', 'EH1', 'S', 'T'], ['T', 'OH1', 'S', 'T'])
    1
    >>> edit_distance('xxxx', 'yyyyyyyy')
    8
    """
    m = len(list1)
    n = len(list2)
    data = [[0 for col in range(n+1)] for row in range(m+1)]
    for col in range(n+1):
        data[0][col] = col
    for row in range(m+1):
        data[row][0] = row
    for a in range(1, m+1):
        for b in range(1, n+1):
            if list1[a-1] == list2[b-1]:
                data[a][b] = data[a-1][b-1]
            else:
                data[a][b] = 1 + min(data[a-1][b], data[a][b-1], data[a-1][b-1])
    return data[m][n]


def longest_match(list1, list2):
    """
    Find the length of the longest substring match between list1 and list2.

    >>> longest_match([], [])
    0
    >>> longest_match('test', 'test')
    4
    >>> longest_match('test', 'toast')
    2
    >>> longest_match('supercalifragilisticexpialidocious', 'mystical californication')
    5
    """
    m = len(list1)
    n = len(list2)
    data = [[0 for col in range(n+1)] for row in range(m+1)]
    for a in range(1, m+1):
        for b in range(1, n+1):
            if list1[a-1] == list2[b-1]:
                data[a][b] = 1 + data[a-1][b-1]
            else:
                data[a][b] = 0
    maxes = [max(row) for row in data]
    return max(maxes)


def prefix_match(list1, list2):
    """
    Find the length of the longest common prefix of list1 and list2.

    >>> prefix_match([], [])
    0
    >>> prefix_match('test', 'test')
    4
    >>> prefix_match('test', 'toast')
    1
    >>> prefix_match('test', 'best')
    0
    >>> prefix_match([1, 2, 3, 4], [1, 2, 4, 8])
    2
    """
    for i in range(min(len(list1), len(list2)), 0, -1):
        if list1[:i] == list2[:i]:
            return i
    return 0


def suffix_match(list1, list2):
    """
    Find the length of the longest common suffix of list1 and list2.
    >>> suffix_match([], [])
    0
    >>> suffix_match('test', 'test')
    4
    >>> suffix_match('test', 'toast')
    2
    >>> suffix_match('test', 'best')
    3
    >>> suffix_match([1, 2, 3, 4], [1, 2, 4, 8])
    0
    """
    for i in range(min(len(list1), len(list2)), 0, -1):
        if list1[-i:] == list2[-i:]:
            return i
    return 0


def scaled_edit_distance_match(list1, list2):
    """
    The inverse edit distance between two lists, as a proportion of their
    minimum length. Think of this as the proportion of the characters
    that don't change when turning list1 into list2.

    >>> scaled_edit_distance_match('test', 'toast')
    0.5
    """
    return 1 - edit_distance(list1, list2) / min(len(list1), len(list2))


def scaled_suffix_match(list1, list2):
    """
    The length of the longest common suffix between two lists, as a
    proportion of their minimum length.

    >>> scaled_suffix_match('test', 'toast')
    0.5
    """
    return suffix_match(list1, list2) / min(len(list1), len(list2))


def scaled_prefix_match(list1, list2):
    """
    The length of the longest common prefix between two lists, as a
    proportion of their minimum length.
    
    >>> scaled_prefix_match('test', 'toast')
    0.25
    """
    return float(prefix_match(list1, list2)) / min(len(list1), len(list2))


def scaled_longest_match(list1, list2):
    """
    The length of the longest substring match between two lists, as a
    proportion of their minimum length.

    >>> scaled_longest_match('test', 'toast')
    0.5
    """
    return longest_match(list1, list2) / min(len(list1), len(list2))


def combined_score(list1, list2):
    """
    A combined measure of the similarity between two lists.

    This measure is the average of the four similarity measures above.
    """
    return (scaled_edit_distance_match(list1, list2)
            + scaled_suffix_match(list1, list2)
            + scaled_prefix_match(list1, list2)
            + scaled_longest_match(list1, list2)) / 4


def _sounds_like_score(text1, text2):
    """
    A measure of the similarity between two texts, via either their
    spelling or their phonetics. The higher this is, the more likely
    it is that one is a 'pun' on the other.
    """
    result = max(combined_score(text1.replace(' ', ''), text2.replace(' ', '')),
                 combined_score(get_phonetic(text1), get_phonetic(text2)))
    return result


def sounds_like_score(target, clue):
    """
    A measure of the similarity between a target word and a 'clue' for that word.
    If the clue as a whole "sounds like" the target word, or each word within it
    does, it is likely that the clue is a pun-based clue, not a meaning-based
    clue.

    >>> sounds_like_score('heat', 'feat meat')
    0.5625
    >>> sounds_like_score('fish', 'chips')
    0.08333333333333333
    """
    subscores = []
    for word in clue.split():
        subscores.append(_sounds_like_score(target, word))
    scores = [_sounds_like_score(target, clue),
              sum(subscores) / len(subscores)]
    return max(scores)


def test(cutoff=0.35):
    """
    Test our heuristics by checking some known positive and negative cases.
    """
    # Positive tests: these should all be greater than the cutoff
    assert sounds_like_score('ham', 'spam') > cutoff
    assert sounds_like_score('research', 're search') > cutoff
    assert sounds_like_score('feet', 'eat') > cutoff
    assert sounds_like_score('mother', 'other') > cutoff
    assert sounds_like_score('fish', 'swish') > cutoff 
    assert sounds_like_score('heat', 'feat meat') > cutoff 
    assert sounds_like_score('love', 'above') > cutoff 
    assert sounds_like_score('love', 'of') > cutoff 

    # Negative tests: these are not sufficiently similar, and should be
    # less than the cutoff
    assert sounds_like_score('spam', 'eggs') < cutoff
    assert sounds_like_score('cow', 'logical') < cutoff
    assert sounds_like_score('sister', 'brother') < cutoff
    assert sounds_like_score('a', 'b') < cutoff 
    assert sounds_like_score('fish', 'chips') < cutoff 
    assert sounds_like_score('behind', 'not') < cutoff 
    assert sounds_like_score('name', 'nomenclature') < cutoff 
    assert sounds_like_score('clothing', 'covering') < cutoff 
    assert sounds_like_score('love', 'of another') < cutoff


if __name__ == '__main__':
    test()
