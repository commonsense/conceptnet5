import codecs
from conceptnet5.edges import make_edge, MultiWriter
from collections import defaultdict



def build_core_from_csvs(csv_files):

    weights = defaultdict(float)
    assertions = {}
    ccby = defaultdict(bool)


    for csv_file in csv_files:
        print "currently in file: " + str(csv_file)
        for line in codecs.open(csv_file, encoding='utf-8'):
            uri, rel, start, end, context, weight, sources, id, dataset = line.split('\t')[:9]
            if uri != 'uri' and context == '/ctx/all':
                weight = float(weight)
                weights[uri] += float(weight)
                assertions[uri] = (rel, start, end, context, weights[uri])
                if not (dataset.startswith('/d/reverb') or dataset.startswith('/d/wiktionary') or dataset.startswith('/d/dbpedia')):
                    ccby[uri] = True

    print 'writing'
    writer_core = MultiWriter('assertion_totals_core')
    #writer_sa = MultiWriter('assertion_totals_sa')

    for uri, weight in assertions.iteritems():
        if ccby[uri]:
            license = '/l/CC/By'
            dataset = '/d/conceptnet/5/combined-core'
        else:
            license = '/l/CC/By-SA'
            dataset = '/d/conceptnet/5/combined-sa'
        relation, start, end, context, weight = assertions[uri]
        edge = make_edge(relation, start, end, dataset, license, ['/s/rule/sum_edges'], '/ctx/all', weight=weight)
        if license == '/l/CC/By':
            writer_core.write(edge)
        #else:
        #    writer_sa.write(edge)
    writer_core.close()
    #writer_sa.close()



if __name__ == '__main__':
    import sys
    csv_files = sys.argv[1:]
    print "building core from the following: \n" + str(csv_files)
    build_core_from_csvs(csv_files)

