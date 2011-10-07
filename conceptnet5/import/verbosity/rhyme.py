from __future__ import with_statement
import numpy as np

phoneticDict = {}
with open('cmudict.0.7a') as rhymelist:
    for line in rhymelist:
        if line.startswith(';;;'): continue
        word, phon = line.strip().split('  ')
        phon = phon.split(' ')
        phoneticDict[word] = phon

def get_phonetic(text):
    parts = []
    for word in text.split():
        parts.extend(phoneticDict.get(word.upper(), list(word.upper())))
    return parts

def edit_distance(list1, list2):
    m = len(list1)
    n = len(list2)
    data = np.zeros((m+1, n+1), 'i')
    data[0,:] = np.arange(n+1)
    data[:,0] = np.arange(m+1)
    data[0,0] = 0
    for a in xrange(1, m+1):
        for b in xrange(1, n+1):
            if list1[a-1] == list2[b-1]:
                data[a,b] = data[a-1,b-1]
            else:
                data[a,b] = 1 + min(data[a-1,b], data[a,b-1], data[a-1,b-1])
    return data[m,n]

def longest_match(list1, list2):
    m = len(list1)
    n = len(list2)
    data = np.zeros((m+1, n+1), 'i')
    for a in xrange(1, m+1):
        for b in xrange(1, n+1):
            if list1[a-1] == list2[b-1]:
                data[a,b] = 1 + data[a-1,b-1]
            else:
                data[a,b] = 0
    return np.max(data)

def prefix_match(list1, list2):
    for i in xrange(min(len(list1), len(list2)), 0, -1):
        if list1[:i] == list2[:i]:
            return i
    return 0

def suffix_match(list1, list2):
    for i in xrange(min(len(list1), len(list2)), 0, -1):
        if list1[-i:] == list2[-i:]:
            return i
    return 0

def scaled_edit_distance(list1, list2):
    # was max
    return 1 - float(edit_distance(list1, list2)) / min(len(list1), len(list2))

def scaled_suffix_match(list1, list2):
    return float(suffix_match(list1, list2)) / min(len(list1), len(list2))

def scaled_prefix_match(list1, list2):
    return float(prefix_match(list1, list2)) / min(len(list1), len(list2))

def scaled_longest_match(list1, list2):
    # was max
    return float(longest_match(list1, list2)) / min(len(list1), len(list2))

def combined_score(list1, list2):
    return (scaled_edit_distance(list1, list2)
            + scaled_suffix_match(list1, list2)
            + scaled_prefix_match(list1, list2)
            + scaled_longest_match(list1, list2)) / 4

def _sounds_like_score(word1, word2):
    result = max(combined_score(word1.replace(' ', ''), word2.replace(' ', '')),
                 combined_score(get_phonetic(word1), get_phonetic(word2)))
    return result

def sounds_like_score(word1, word2):
    subscores = []
    for subword in word2.split():
        subscores.append(_sounds_like_score(word1, subword))
    scores = [_sounds_like_score(word1, word2),
              sum(subscores)/len(subscores)]
    return max(scores)

def test(cutoff=0.35):
    print combined_score('love', 'of')
    assert get_phonetic('cow') == ['K', 'AW1']
    assert sounds_like_score('ham', 'spam') > cutoff
    assert sounds_like_score('research', 're search') > cutoff
    assert sounds_like_score('spam', 'eggs') < cutoff
    assert sounds_like_score('cow', 'lojbanistan') < cutoff
    assert sounds_like_score('feet', 'eat') > cutoff
    assert sounds_like_score('sister', 'brother') < cutoff
    assert sounds_like_score('mother', 'other') > cutoff
    assert sounds_like_score('a', 'b') < cutoff 
    assert sounds_like_score('fish', 'chips') < cutoff 
    assert sounds_like_score('fish', 'swish') > cutoff 
    assert sounds_like_score('behind', 'not') < cutoff 
    assert sounds_like_score('name', 'nomenclature') < cutoff 
    assert sounds_like_score('clothing', 'covering') < cutoff 
    assert sounds_like_score('heat', 'feat meat') > cutoff 
    assert sounds_like_score('love', 'above') > cutoff 
    assert sounds_like_score('love', 'of') > cutoff 
    assert sounds_like_score('love', 'of another') < cutoff 

if __name__ == '__main__':
    test()
