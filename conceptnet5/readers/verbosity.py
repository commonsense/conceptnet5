from conceptnet5.uri import concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.json_writer import FlatEdgeWriter
from conceptnet5.readers.sounds_like import sounds_like_score
from collections import defaultdict
import re
import sys

BAD_CLUE_REGEX = re.compile(
    r'(^letter|^rhyme|^blank$|^word$|^syllable$|^spell|^tense$|^prefix'
    r'|^suffix|^guess|^starts?$|^ends?$|^singular$|^plural|^noun|^verb'
    r'|^opposite|^homonym$|^synonym$|^antonym$|^close$|^only$|^just$|'
    r'^different|^this$|^that$|^these$|^those$|^mince$|^said$|^same$)'
)

def run_verbosity(infile, outfile):
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
            if BAD_CLUE_REGEX.match(rword):
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

            #weight = math.log(1 + score/10.0) / math.log(2)
            weight = score / 100.0

            count += 1
            counts['success'] += 1
            
            leftc = concept_uri('en', left)
            rightc = concept_uri('en', rightword)
            edge = make_edge(rel, leftc, rightc, '/d/verbosity',
                             '/l/CC/By', sources, surfaceText=text,
                             weight=weight)
            writer.write(edge)

if __name__ == '__main__':
    run_verbosity(sys.argv[1], sys.argv[2])
