import sys
import json
import random
random.seed(0)

def reduce_concept(concept):
    parts = concept.split(u'/')
    # Unify simplified and traditional Chinese in associations.
    if parts[2] == 'zh_CN' or parts[2] == 'zh_TW':
        parts[2] = 'zh'
    return u'/'.join(parts[:4])

def convert_to_word2vec(in_stream=None, out_stream=None):
    if in_stream is None:
        in_stream = sys.stdin
    if out_stream is None:
        out_stream = sys.stdout
    
    texts = []
    for line in in_stream:
        if not line.strip():
            continue
        entry = json.loads(line.strip().decode('utf-8'))
        weight = float(entry['weight']) * 2
        if weight < 1:
            continue
        start = reduce_concept(entry['start'])
        end = reduce_concept(entry['end'])
        outline = u"%s %s %s </s>" % (start, entry['rel'], end)
        for iteration in range(int(weight)):
            texts.append(outline)

    random.shuffle(texts)
    for text in texts:
        print >> out_stream, text.encode('utf-8')

if __name__ == '__main__':
    convert_to_word2vec()
