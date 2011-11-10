from conceptnet5.english_nlp import normalize
from conceptnet5.graph import JSONWriterGraph
from rhyme import sounds_like_score
from collections import defaultdict
import math, re

make_json = True

assertions = []

mapping = {
    "it is typically near": '/concept/en/be_near',
    "it is typically in": '/concept/en/be_in',
    "it is used for": '/relation/UsedFor',
    "it is a kind of": '/relation/IsA',
    "it is a type of": '/relation/IsA',
    "it is about the same size as": '/relation/RelatedTo',
    "it is related to": '/relation/RelatedTo',
    "it has": '/concept/en/have_or_involve',
    "it is": '/relation/HasProperty',
    "it looks like": '/concept/en/look_like',
}

bad_regex_no_biscuit =\
  re.compile(r'(^letter|^rhyme|^blank$|^word$|^syllable$|^spell$|^tense$|^prefix|^suffix|^guess|^starts?$|^ends?$|^singular$|^plural|^noun|^verb|^opposite|^homonym$|^synonym$|^antonym$|^close$|^only$|^just$|^different|^this$|^that$|^these$|^those$|^mince$|^said$|^same$)')

maxscore = 0
count = 0
skipcount = 0
counts = defaultdict(int)
text_similarities = []

flag_out = open('output/flagged_assertions.txt', 'w')
similar_out = open('output/text_similarity.txt', 'w')
weak_out = open('output/weak_assertions.txt', 'w')
good_out = open('output/ok_assertions.txt', 'w')

GRAPH = None
context = source = None
if make_json:
    GRAPH = JSONWriterGraph('../json_data/verbosity')
    source = GRAPH.get_or_create_node('/source/site/verbosity')
    context = GRAPH.get_or_create_node('/context/General')
    GRAPH.justify(0, source)

for line in open('verbosity.txt'):
    if skipcount > 0:
        skipcount -= 1
        continue
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
        print "FLAGGED:", right
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
    if rel is None:
        rel = '/concept/en/'+normalize(relation[3:]).replace(' ', '_')
    
    if relation == 'it is' and\
       (right.startswith('a ') or right.startswith('an ')
        or right.startswith('the ')):
        rel = '/relation/IsA'
    
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
    if count % 100 == 0:
        print (rel, left, right, score)
    
    if make_json:
        left_concept = GRAPH.get_or_create_concept('en', left)
        right_concept = GRAPH.get_or_create_concept('en', right)
        relation = GRAPH.get_or_create_node(rel)
        assertion = GRAPH.get_or_create_assertion(
            relation,
            [left_concept, right_concept],
            {'dataset': 'verbosity', 'license': 'CC-By'}
        )
        GRAPH.justify(source, assertion, weight=score/10.0)
        GRAPH.add_context(assertion, context)

print counts

flag_out.close()
good_out.close()
weak_out.close()
similar_out.close()

simout = open('similarity-scores.txt', 'w')
for sim in text_similarities:
    print >> simout, sim
simout.close()
