import codecs
from conceptnet5.edges import make_edge, MultiWriter
from collections import defaultdict

weights = defaultdict(float)
counts = defaultdict(int)
assertions = {}
seen = set()

for line in codecs.open('data/flat/CORE', encoding='utf-8'):
    uri, rel, start, end, context, weight, sources, id, dataset = line.split('\t')[:9]
    if uri != 'uri' and context == '/ctx/all':
        if uri not in seen:
            seen.add(uri)
            weight = float(weight)
            weights[uri] += float(weight)
            counts[start] += 1
            counts[end] += 1
            assertions[uri] = (rel, start, end, context, weight)

print 'writing'
gephi = codecs.open('data/links-core.csv', 'w', encoding='utf-8')
print >> gephi, 'Source,Target,Weight'

for uri, weight in weights.iteritems():
    rel, start, end, context, weight = assertions[uri]
    if counts[start] > 1 and counts[end] > 1:
        print >> gephi, '%s\t%s' % (start.replace('"', '_'), end.replace('"', '_'))
gephi.close()

