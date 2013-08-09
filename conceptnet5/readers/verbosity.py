from conceptnet5.nodes import normalize_uri, make_concept_uri
from conceptnet5.edges import FlatEdgeWriter, make_edge
from collections import defaultdict
import math, re
import sys
from conceptnet5.readers.rhyme import sounds_like_score


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
  re.compile(r'(^letter|^rhyme|^blank$|^word$|^syllable$|^spell$|^tense$|^prefix|^suffix|^guess|^starts?$|^ends?$|^singular$|^plural|^noun|^verb|^opposite|^homonym$|^synonym$|^antonym$|^close$|^only$|^just$|^different|^this$|^that$|^these$|^those$|^mince$|^said$|^same$)')

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

        if right.startswith('not '):
            right = right[4:]
            relation = 'it is not'
        if relation == 'it is the opposite of':
            relation = 'it is not'

        freq = int(freq)
        orderscore = int(orderscore)
        if relation == 'about the same size as':
            relation = 'it is about the same size as'
        elif relation == 'it looks like':
            relation = 'it is related to'
        rel = mapping.get(relation)
        reltext = relation[3:]
        if rel is None:
            rel = make_concept_uri(unicode(reltext), 'en')
        text = '[[%s]] %s [[%s]]' % (left, reltext, right)
        
        if relation == 'it is' and\
           (right.startswith('a ') or right.startswith('an ')
            or right.startswith('the ')):
            rel = '/r/IsA'
        
        sls = sounds_like_score(left, right)
        text_similarities.append(sls)
        if sls > 0.35:
            #print "* %s sounds like %s (%4.4f)" % (left, right, sls)
            counts['text similarity'] += 1
            continue
        
        score = (freq*2-1) * (1000-orderscore) * (1-sls) / 1000
        if score <= 0:
            counts['low score'] += 1
            continue

        count += 1
        counts['success'] += 1
        
        left = make_concept_uri(unicode(left), 'en')
        right = make_concept_uri(unicode(right), 'en')
        edge = make_edge(rel, left, right, '/d/verbosity',
                         '/l/CC/By', sources, surfaceText=text,
                         weight = score/10.0)
        writer.write(edge)

        writer.close()

if __name__ == '__main__':
    run_verbosity(sys.argv[1], sys.argv[2])
