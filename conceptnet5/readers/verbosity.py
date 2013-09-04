from conceptnet5.nodes import normalize_uri, make_concept_uri
from conceptnet5.edges import FlatEdgeWriter, make_edge
from collections import defaultdict
import math, re
import sys
from conceptnet5.readers.rhyme import sounds_like_score

# We were using this at one point, but it turns out that people don't use any
# relation on Verbosity consistently. Instead we make them all /r/RelatedTo,
# the most general one, except for the negated ones which we make /r/Antonym.
mapping = {
    "it is typically near": '/c/en/be_near',
    "it is typically in": '/c/en/be_in',
    "it is used for": '/r/UsedFor',
    "it is a kind of": '/r/IsA',
    "it is a type of": '/r/IsA',
    "it is about the same size as": '/r/RelatedTo',
    "it is related to": '/r/RelatedTo',
    "it has": '/c/en/have_or_involve',
    "it is": '/r/HasProperty',
    "it looks like": '/c/en/look_like',
}

bad_regex_no_biscuit =\
  re.compile(r'(^letter|^rhyme|^blank$|^word$|^syllable$|^spell|^tense$|^prefix|^suffix|^guess|^starts?$|^ends?$|^singular$|^plural|^noun|^verb|^opposite|^homonym$|^synonym$|^antonym$|^close$|^only$|^just$|^different|^this$|^that$|^these$|^those$|^mince$|^said$|^same$)')

def run_verbosity(infile, outfile):
    maxscore = 0
    count = 0
    counts = defaultdict(int)
    text_similarities = []

    sources = ['/s/site/verbosity']

    writer = FlatEdgeWriter(outfile)

    for line in open(infile):
        parts = line.strip().split('\t')
        if not parts:
            counts['blank'] += 1
            continue
        left, relation, right, freq, orderscore = parts[:5]


        # catch bad stuff
        flagged = False

        for rword in right.split():
            if bad_regex_no_biscuit.match(rword):
                flagged = True
                break
        if flagged:
            #print "FLAGGED:", right
            counts['flag word'] += 1
            continue
        if len(right) < 3:
            counts['clue too short'] += 1
            continue
        if len(right.split()[-1]) == 1:
            counts['letter'] += 1
            continue
        if right.startswith('add') or right.startswith('delete') or right.startswith('remove'):
            counts['flag word'] += 1
            continue

        freq = int(freq)
        orderscore = int(orderscore)
        rel = '/r/RelatedTo'
        reltext = 'is related to'
        if right.startswith('not '):
            rel = '/r/Antonym'
            right = right[4:]
            reltext = 'is not'
        if relation == 'it is the opposite of':
            rel = '/r/Antonym'
            reltext = 'is the opposite of'

        rightwords = [right]
        if ' ' in right:
            rightwords.extend(right.split(' '))

        sls = sounds_like_score(left, right)
        text_similarities.append(sls)
        if sls > 0.35:
            counts['text similarity'] += 1
            continue
        
        for i, rightword in enumerate(rightwords):
            edge_sources = list(sources)
            if i > 0:
                edge_sources.append('/s/rule/split_words')
            text = '[[%s]] %s [[%s]]' % (left, reltext, rightword)
            
            sls = sounds_like_score(left, rightword)
            text_similarities.append(sls)
            if sls > 0.35:
                counts['text similarity'] += 1
                continue
            
            score = (freq*2-1) * (1000-orderscore) * (1-sls) / 1000
            if score <= 0:
                counts['low score'] += 1
                continue

            count += 1
            counts['success'] += 1
            
            leftc = make_concept_uri(unicode(left), 'en')
            rightc = make_concept_uri(unicode(rightword), 'en')
            edge = make_edge(rel, leftc, rightc, '/d/verbosity',
                             '/l/CC/By', sources, surfaceText=text,
                             weight = score/10.0)
            writer.write(edge)

if __name__ == '__main__':
    run_verbosity(sys.argv[1], sys.argv[2])
