from conceptnet.models import *
import os
import codecs
import sys
from conceptnet5.nodes import make_concept_uri
from conceptnet5.edges import make_edge, MultiWriter
from quick_reader import QuickReader


def handle_raw_assertion(raw_assertion):
    line = raw_assertion.strip()
    edges = []
    if line:
        parts = line.split(', ')
        user, frame_id, concept1, concept2 = parts
        frame = Frame.objects.get(id=int(frame_id))
        ftext = frame.text
        relation = frame.relation.name
        rel = '/r/'+relation

        surfaceText = ftext.replace(u'{1}', u'[['+concept1+u']]').replace(u'{2}', u'[['+concept2+u']]')
        start = make_concept_uri(concept1, 'zh_TW')
        end = make_concept_uri(concept2, 'zh_TW')
        sources = ['/s/contributor/petgame/'+user, '/s/activity/ntt/petgame']
        edge = make_edge(rel, start, end, dataset='/d/conceptnet/4/zh',
                         license='/l/CC/By', sources=sources,
                         surfaceText=surfaceText, weight=1)
        edges.append(edge)
    return edges

def add_lines_to_queue(q):
    path = "./raw_data/"
    for filename in os.listdir(path):
        for line in codecs.open(path + filename, encoding='utf-8', errors='replace'):
            q.put(line)

def run_single_process():
    writer = MultiWriter('conceptnet4_zh')
    path = "./raw_data/"
    for filename in os.listdir(path):
        for line in codecs.open(path + filename, encoding='utf-8', errors='replace'):
            edges = handle_raw_assertion(line)
            for edge in edges:
                writer.write(edge)


if __name__ == '__main__':
    if "--quick_write" in sys.argv:
        quickReader = QuickReader("conceptnet4_zh", handle_raw_assertion,add_lines_to_queue)
        quickReader.start()

    else:
        run_single_process()