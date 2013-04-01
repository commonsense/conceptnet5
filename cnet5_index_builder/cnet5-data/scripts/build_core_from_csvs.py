import codecs
from conceptnet5.edges import make_edge, MultiWriter
from collections import defaultdict
from multiprocessing import Process
import time
import os
import sys

N = 100
CURRENT_DIR = os.getcwd()

def build_core_from_csvs(csv_files):

    for csv_file in csv_files:
        sort_assertions(csv_file)

    for assertions_file_index in range(N):
        sum_assertions(assertions_file_index)
        

#this hashes all the uri's and places them
#into smaller grouping of uri's that have the
#same hash, that way we can them sum up all the weights for
#each one of these files without having to pull all 
#assertions into memory at the same time.
def sort_assertions(csv_file):
    for line in codecs.open(csv_file, encoding='utf-8'):
        uri, rel, start, end, context, weight, sources, id, dataset = line.split('\t')[:9]
        uri_index = hash(uri)%N
        f = codecs.open(CURRENT_DIR +'/data/temp/core_'+str(uri_index)+'.txt', 'a','utf-8')
        f.write(line)
        f.close()


def sum_assertions(file_index):
    weights = defaultdict(float)
    assertions = {}
    ccby = defaultdict(bool)

    for line in codecs.open(CURRENT_DIR +'/data/temp/core_'+str(file_index)+'.txt', 'r','utf-8'):
        uri, rel, start, end, context, weight, sources, id, dataset = line.split('\t')[:9]
        if uri != 'uri' and context == '/ctx/all':
            weight = float(weight)
            weights[uri] += float(weight)
            assertions[uri] = (rel, start, end, context, weights[uri])
            if not (dataset.startswith('/d/reverb') or dataset.startswith('/d/wiktionary') or dataset.startswith('/d/dbpedia')):
                ccby[uri] = True


    writer_core = MultiWriter('assertion_totals_core')
    #writer_sa = MultiWriter('assertion_totals_sa')
    for uri, values in assertions.iteritems():
        relation, start, end, context, weight = values
        if ccby[uri]:
            license = '/l/CC/By'
            dataset = '/d/conceptnet/5/combined-core'
        else:
            license = '/l/CC/By-SA'
            dataset = '/d/conceptnet/5/combined-sa'
        edge = make_edge(relation, start, end, dataset, license, ['/s/rule/sum_edges'], '/ctx/all', weight=weight)
        if license == '/l/CC/By':
            writer_core.write(edge)
        #else:
            #writer_sa.write(edge)
    writer_core.close()
    #writer_sa.close()


if __name__ == '__main__':
    csv_files = sys.argv[1:]
    print "building core from the following: \n" + str(csv_files)
    build_core_from_csvs(csv_files)
    print "finished building the core"

