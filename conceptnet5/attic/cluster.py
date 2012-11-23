### Because of NLTK performance issues, a cache is highly recommended.
### To make a cache, comment out the block with "NOTE: Use to make map" and call the method make_map()
### When you already have a cache, comment out the line with "NOTE: Use when have map",
### run this file, then call the method cluster()
### 
### Sample input file: (The parts after "<--" in each line should not be in the input file.)
### 30 <-- Number of words
### 
### cottage 3 <-- First word "cottage" has 3 senses
### 1 <-- Number of lines of description for this sense
### A_small_house <-- Sense
### 1 <-- Number of lines of description for this sense
### Upper_Marlboro,_Maryland <-- Sense
### 1 <-- Number of lines of description for this sense
### film <-- Sense
### 0 0 <-- Gold standard on whether the 1st and 2nd senses are similar, respectively with 1st and 3rd
### 0 <-- Gold standard on whether the 2nd and 3rd senses are similar
###
### minor 16 <-- Second word "minor" has 16 senses
### ...

import freq_map, re, math
from sim_map_training import sim_map_training # NOTE: Use when have map
from nltk.corpus import wordnet

'''returns the log coefficient of a word
coefficient of 'the' = 0.22, coefficient of a word that occurs once = 0.95'''
def freq_coeff(word):
    base = 1000000 # approximate total number of word occurrences
    numerator = 1000000.0
    freq = 1
    if word in freq_map.freq_map:
        freq += freq_map.freq_map[word]
    return math.log(numerator/freq, base)

# NOTE: Use to make map
#filewrite = open('sim_map_training.py', 'w') 
#sim_map = {} 
# END NOTE: Use to make map

'''returns the similarity of two words based on Wu-Palmer similarities'''
def word_similarity_wup(word1, word2, makemap=False):
    if makemap:
        if (word1, word2) in sim_map:
            return sim_map[(word1, word2)]
        if (word2, word1) in sim_map:
            return sim_map[(word2, word1)]
    else:
        if (word1, word2) in sim_map_training: 
            return sim_map_training[(word1, word2)]
        if (word2, word1) in sim_map_training:
            return sim_map_training[(word2, word1)]
    synset_list1 = wordnet.synsets(word1)
    synset_list2 = wordnet.synsets(word2)
    if len(synset_list1) == 0 or len(synset_list2) == 0:
        return 0
    ans = 0.0
    for synset1 in synset_list1:
        for synset2 in synset_list2:
            sim = wordnet.wup_similarity(synset1, synset2)
            ans = max(ans, sim)
    if ans > 0.99:
        ans = 1.25
    if makemap:
        sim_map[(word1, word2)] = ans 
        filewrite.write("('"+word1+"','"+word2+"'):"+str(ans)+',\n') 
    return ans

'''returns the similarity of the words in two lists based on
Wu-Palmer similarities, with one list used as the main one'''
def wordlist_similarity_wup_oneway(list1, list2, makemap=False):
    totsim = 0.0
    totdiv = 0.0
    for word1 in list1:
        maxsim = 0
        for word2 in list2:
            if word_similarity_wup(word1, word2, makemap) > maxsim:
                maxsim = word_similarity_wup(word1, word2, makemap)
        totsim += maxsim * freq_coeff(word1)
        totdiv += freq_coeff(word1)
    if abs(totdiv) < 0.00001:
        return 1
    return totsim/totdiv

'''returns the similarity of the words in two list based on
Wu-Palmer similarities'''
def wordlist_similarity_wup(list1, list2, makemap=False):
    sim1 = wordlist_similarity_wup_oneway(list1, list2, makemap)
    sim2 = wordlist_similarity_wup_oneway(list2, list1, makemap)
    return (sim1+sim2)/2.0

''' align all pairs of descriptions of a word, and return the number
of true positives, false positives, and false negatives '''
def align_descriptions(desc_array, ans_array, threshold, makemap=False):
    num = len(desc_array)
    true_pos = 0
    false_pos = 0
    false_neg = 0
    for i in range(num):
        for j in range(i+1, num):
            word1 = desc_array[i][0]
            word2 = desc_array[j][0]
            desc1 = desc_array[i][1]
            desc2 = desc_array[j][1]
            sim = wordlist_similarity_wup(desc1, desc2, makemap)
            guess = (sim >= threshold)
            forbidden = [['film'], ['novel'], ['musical'], \
                         ['band'], ['town'], ['album'], \
                         ['company'], ['book'], ['movie'], \
                         ['song'], ['Song'], ['series']]
            for forbidden_list in forbidden:
                if forbidden_list[0] in desc1 or forbidden_list[0] in desc2:
                    guess = 0
            ans = ans_array[i][j-i-1]
            if guess == 1 and ans == 1:
                true_pos += 1
            if guess == 1 and ans == 0:
                false_pos += 1
            if guess == 0 and ans == 1:
                false_neg += 1
    return (true_pos, false_pos, false_neg)           

''' Read an input file, and align all pairs of descriptions of all words '''
def align_input(filename, threshold, makemap=False):
    fileread = open(filename, 'r')
    numlines = int(fileread.readline())
    fileread.readline() # read blank line
    true_pos = 0
    false_pos = 0
    false_neg = 0

    for i in range(numlines):
        firstline = fileread.readline()
        firstarray = re.compile(r'\s').split(firstline)
        word = firstarray[0] # current word
        numdescs = int(firstarray[1]) # number of descriptions
        # e.g. desc_array =
        # [('A_small_house', ['A', 'small', 'house']),
        # ('Upper_Marlboro,_Maryland', ['Upper', 'Marlboro,', 'Maryland']),
        # ('film', ['film'])]
        desc_array = []
        for j in range(numdescs):
            numlines = int(fileread.readline())
            desc = fileread.readline()[:-1] # remove newline
            # e.g. desc_wordarray = ['A', 'small', 'house']
            desc_wordarray = re.compile(r'_').split(desc)
            for k in range(numlines-1):
                additional_desc = fileread.readline()[:-1]
                additional_desc_wordarray = \
                    re.compile(r'_').split(additional_desc)
                desc_wordarray += additional_desc_wordarray
            desc_array.append((desc, desc_wordarray))
        # e.g. ans_array = [['0', '1'], ['0']]
        ans_array = [] # answer key as inputted
        for j in range(numdescs-1):
            ans = fileread.readline()[:-1]
            ans_line = re.compile(r'\s').split(ans)
            for k in range(len(ans_line)):
                ans_line[k] = int(ans_line[k]) # convert to int
            ans_array.append(ans_line)
        fileread.readline()
        res = align_descriptions(desc_array, ans_array, threshold, makemap)
        true_pos += res[0]
        false_pos += res[1]
        false_neg += res[2]
        print res

    print (true_pos, false_pos, false_neg)
    precision = float(true_pos)/(true_pos + false_pos)
    recall = float(true_pos)/(true_pos + false_neg)
    print (precision, recall, (2*precision*recall)/(precision+recall))

    fileread.close()

''' produce the cache from the input '''
def make_map():
    filewrite.write('sim_map_training = {\n') 
    align_input('machine_training.txt', 0.64, True)
    filewrite.write('}') 
    filewrite.close()

''' do the actual clustering '''
def cluster():
    threshold_list = [0.01*x for x in range(60, 70)] 
    for threshold in threshold_list: 
        print "THRESHOLD = " + str(threshold) 
        align_input('machine_training.txt', threshold) 

if __name__ == '__main__':
    pass
    
