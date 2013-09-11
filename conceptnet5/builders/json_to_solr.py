import json
import sys
from conceptnet5.edges import SolrEdgeWriter

def reduce_concept(concept):
    parts = concept.split(u'/')
    # Unify simplified and traditional Chinese in associations.
    if parts[2] == 'zh_CN' or parts[2] == 'zh_TW':
        parts[2] = 'zh'
    return u'/'.join(parts[:4])

def convert_to_solr(in_stream=None, out_stream=None):
    if in_stream is None:
        in_stream = sys.stdin
    if out_stream is None:
        out_stream = sys.stdout

    writer = SolrEdgeWriter(out_stream)
    
    for line in in_stream:
        if not line.strip():
            continue
        info = json.loads(line.strip().decode('utf-8'))
        writer.write(info)
    writer.close()

if __name__ == '__main__':
    convert_to_solr()
