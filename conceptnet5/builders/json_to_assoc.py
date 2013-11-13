import json
import sys

def reduce_concept(concept):
    parts = concept.split(u'/')
    # Unify simplified and traditional Chinese in associations.
    if parts[2] == 'zh_CN' or parts[2] == 'zh_TW':
        parts[2] = 'zh'
    return u'/'.join(parts[:4])

def convert_to_assoc(in_stream=None, out_stream=None):
    if in_stream is None:
        in_stream = sys.stdin
    if out_stream is None:
        out_stream = sys.stdout
    
    for line in in_stream:
        if not line.strip():
            continue
        info = json.loads(line.strip().decode('utf-8'))
        startc = reduce_concept(info[u'start'])
        endc = reduce_concept(info[u'end'])
        rel = info[u'rel']
        weight = info[u'weight']

        if u'dbpedia' in info[u'sources'] and u'/or/' not in info[u'sources']:
            # DBPedia associations are still too numerous and too weird to
            # associate.
            continue

        pairs = []
        if startc == u'/c/en/person':
            if rel == u'/r/Desires':
                pairs = [(u'/c/en/good', endc), (u'/c/en/bad/neg', endc)]
            elif rel == u'/r/NotDesires':
                pairs = [(u'/c/en/bad', endc), (u'/c/en/good/neg', endc)]
            else:
                pairs = [(startc, endc)]
        elif startc == u'/c/zh/人':
            if rel == u'/r/Desires':
                pairs = [(u'/c/zh/良好', endc), (u'/c/zh/不良/neg', endc)]
            elif rel == '/r/NotDesires':
                pairs = [(u'/c/zh/良好/neg', endc), (u'/c/zh/不良', endc)]
            else:
                pairs = [(startc, endc)]
        else:
            negated = (rel.startswith(u'/r/Not') or rel.startswith(u'/r/Antonym'))
            if not negated:
                pairs = [(startc, endc)]
            else:
                pairs = [(startc, endc + u'/neg'), (startc + u'/neg', endc)]

        for (start, end) in pairs:
            line = u"%(start)s\t%(end)s\t%(weight)s" % {
                u'start': start,
                u'end': end,
                u'weight': weight,
            }
            print >> out_stream, line.encode('utf-8')

if __name__ == '__main__':
    convert_to_assoc()
