import json
import sys

def convert_to_tab_separated(in_stream=None, out_stream=None):
    if in_stream is None:
        in_stream = sys.stdin
    if out_stream is None:
        out_stream = sys.stdout
    
    for line in in_stream:
        if not line.strip():
            continue
        info = json.loads(line.strip().decode('utf-8'))
        text = info.get(u'surfaceText') or ''

        line = "%(uri)s\t%(rel)s\t%(start)s\t%(end)s\t%(context)s\t%(weight)s\t%(sources)s\t%(id)s\t%(dataset)s\t%(text)s" % {
            'uri': info[u'uri'],
            'rel': info[u'rel'],
            'start': info[u'start'],
            'end': info[u'end'],
            'context': info[u'context'],
            'weight': info[u'weight'],
            'sources': info[u'sources'],
            'id': info[u'id'],
            'text': text,
            'dataset': info[u'dataset'],
        }
        print >> out_stream, line.encode('utf-8')

if __name__ == '__main__':
    convert_to_tab_separated()
