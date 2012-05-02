import codecs
from conceptnet5.edges import make_edge, MultiWriter
from collections import defaultdict

weights = defaultdict(float)
assertions = {}
ccby = defaultdict(bool)

for line in codecs.open('data/flat/ALL2.csv', encoding='utf-8'):
    uri, rel, start, end, context, weight, sources, id, dataset = line.split('\t')[:9]
    if uri != 'uri' and context == '/ctx/all':
        weight = float(weight)
        weights[uri] += float(weight)
        assertions[uri] = (rel, start, end, context, weight)
        if not (dataset.startswith('/d/reverb') or dataset.startswith('/d/wiktionary') or dataset.startswith('/d/dbpedia')):
            ccby[uri] = True

print 'writing'
writer_core = MultiWriter('assertion_totals_core')
writer_sa = MultiWriter('assertion_totals_sa')
gephi = codecs.open('data/flat/links.csv', 'w', encoding='utf-8')
print >> gephi, 'Source,Target,Weight'

for uri, weight in assertions.iteritems():
    if ccby[uri]:
        license = '/l/CC/By'
        dataset = '/d/conceptnet/5/combined-core'
    else:
        license = '/l/CC/By-SA'
        dataset = '/d/conceptnet/5/combined-sa'
    relation, start, end, context, weight = assertions[uri]
    edge = make_edge(relation, start, end, dataset, license, ['/s/rule/sum_edges'], '/ctx/all', weight=weight)
    print >> gephi, '"%s","%s","%s"' % (start.replace('"', '_'), end.replace('"', '_'), weight)
    if license == '/l/CC/By':
        writer_core.write(edge)
    else:
        writer_sa.write(edge)
gephi.close()
writer_core.close()
writer_sa.close()

