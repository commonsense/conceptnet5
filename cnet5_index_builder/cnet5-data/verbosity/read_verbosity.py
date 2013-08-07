from conceptnet5.nodes import normalize_uri, make_concept_uri
from conceptnet5.edges import MultiWriter, make_edge
from collections import defaultdict
import math, re
import sys
sys.path.append("./scripts")
from rhyme import sounds_like_score

make_json = True

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

maxscore = 0
count = 0

counts = defaultdict(int)
text_similarities = []

flag_out = open('data/output/flagged_assertions.txt', 'w')
similar_out = open('data/output/text_similarity.txt', 'w')
weak_out = open('data/output/weak_assertions.txt', 'w')
good_out = open('data/output/ok_assertions.txt', 'w')
sources = ['/s/site/verbosity']




writer = None
if make_json:
    writer = MultiWriter('verbosity')

for line in open('raw_data/verbosity.txt'):

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
        flag_out.write(line)
        continue
    if len(right) < 3:
        counts['clue too short'] += 1
        flag_out.write(line)
        continue
    if len(right.split()[-1]) == 1:
        counts['letter'] += 1
        flag_out.write(line)
        continue
    if right.startswith('add') or right.startswith('delete') or right.startswith('remove'):
        counts['flag word'] += 1
        flag_out.write(line)
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
        similar_out.write('%4.4d\t%s' % (sls, line))
        continue
    
    score = (freq*2-1) * (1000-orderscore) * (1-sls) / 1000
    if score <= 0:
        counts['low score'] += 1
        weak_out.write(line)
        continue

    count += 1
    counts['success'] += 1
    good_out.write(line)
    
    if make_json:
        left = make_concept_uri(unicode(left), 'en')
        right = make_concept_uri(unicode(right), 'en')
        edge = make_edge(rel, left, right, '/d/verbosity',
                         '/l/CC/By', sources, surfaceText=text,
                         weight = score/10.0)
        writer.write(edge)


if make_json:
    writer.close()

flag_out.close()
good_out.close()
weak_out.close()
similar_out.close()

simout = open('data/output/similarity-scores.txt', 'w')
for sim in text_similarities:
    print >> simout, sim
simout.close()
