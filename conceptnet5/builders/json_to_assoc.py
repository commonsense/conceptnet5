from __future__ import unicode_literals, print_function
from conceptnet5.uri import join_uri, split_uri
import json
import sys

def reduce_concept(concept):
    """
    Remove the part of speech and disambiguation (if present) from a concept,
    leaving a potentially ambiguous concept that can be matched against surface
    text.

    Additionally, remove the region tag from Chinese assertions, so they are
    considered simply as assertions about Chinese regardless of whether it is
    Traditional or Simplified Chinese. In the cases where they overlap, this
    helps to make the information more complete.
    """
    parts = split_uri(concept)
    # Unify simplified and traditional Chinese in associations.
    if parts[1] == 'zh_CN' or parts[1] == 'zh_TW':
        parts[1] = 'zh'
    return join_uri(*parts[:3])

def convert_to_assoc(in_stream=None, out_stream=None):
    if in_stream is None:
        in_stream = sys.stdin
    if out_stream is None:
        out_stream = sys.stdout
    
    for line in in_stream:
        if not line.strip():
            continue
        info = json.loads(line.strip().decode('utf-8'))
        startc = reduce_concept(info['start'])
        endc = reduce_concept(info['end'])
        rel = info['rel']
        weight = info['weight']

        if 'dbpedia' in info['sources'] and '/or/' not in info['sources']:
            # DBPedia associations are still too numerous and too weird to
            # associate.
            continue

        pairs = []
        if startc == '/c/en/person':
            if rel == '/r/Desires':
                pairs = [('/c/en/good', endc), ('/c/en/bad/neg', endc)]
            elif rel == '/r/NotDesires':
                pairs = [('/c/en/bad', endc), ('/c/en/good/neg', endc)]
            else:
                pairs = [(startc, endc)]
        elif startc == '/c/zh/人':
            if rel == '/r/Desires':
                pairs = [('/c/zh/良好', endc), ('/c/zh/不良/neg', endc)]
            elif rel == '/r/NotDesires':
                pairs = [('/c/zh/良好/neg', endc), ('/c/zh/不良', endc)]
            else:
                pairs = [(startc, endc)]
        else:
            negated = (rel.startswith('/r/Not') or rel.startswith('/r/Antonym'))
            if not negated:
                pairs = [(startc, endc)]
            else:
                pairs = [(startc, endc + '/neg'), (startc + '/neg', endc)]

        for (start, end) in pairs:
            line = "%(start)s\t%(end)s\t%(weight)s" % {
                'start': start,
                'end': end,
                'weight': weight,
            }
            print >> out_stream, line.encode('utf-8')

if __name__ == '__main__':
    convert_to_assoc()
