import json
import codecs

def convert_to_tab_separated(name):
    if name.endswith('.json'):
        name = name[:-5]
    infile = open('%s.json' % name)
    outfile = codecs.open('%s.csv' % name, 'w', encoding='utf-8')
    print >> outfile, "uri\trel\tstart\tend\tcontext\tweight\tsources\tid"
    for line in infile:
        info = json.loads(line)
        print info[u'uri']

        print >> outfile, "%(uri)s\t%(rel)s\t%(start)s\t%(end)s\t%(context)s\t%(weight)s\t%(sources)s\t%(id)s" % {
            'uri': info[u'uri'],
            'rel': info[u'rel'],
            'start': info[u'start'],
            'end': info[u'end'],
            'context': info[u'context'],
            'weight': info[u'weight'],
            'sources': ','.join(info[u'sources']),
            'id': info[u'id'],
        }

if __name__ == '__main__':
    import sys
    convert_to_tab_separated(sys.argv[1])

