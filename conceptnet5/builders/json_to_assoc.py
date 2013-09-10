import json
import sys

def reduce_concept(concept):
    parts = concept.split(u'/')
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

        if rel == '/r/Desires':
            pairs = [('/c/en/good', endc), ('/c/en/bad/neg', endc)]
        elif rel == '/r/NotDesires':
            pairs = [('/c/en/bad', endc), ('/c/en/good/neg', endc)]
        else:
            negated = (rel.startswith('/r/Not') or rel.startswith('/r/Antonym'))
            if not negated:
                pairs = [(startc, endc)]
            else:
                pairs = [(startc, endc + '/neg'), (startc + '/neg', endc)]

        for (start, end) in pairs:
            line = u"%(start)s\t%(end)s\t%(weight)s" % {
                u'start': start,
                u'end': end,
                u'weight': weight,
            }
            print >> out_stream, line.encode('utf-8')

if __name__ == '__main__':
    convert_to_assoc()
