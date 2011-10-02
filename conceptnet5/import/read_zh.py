from conceptnet.models import Frame
from conceptnet5.graph import get_graph
import os
import codecs

GRAPH = get_graph()

def handle_file(filename):
    petgame = GRAPH.get_or_create_node(u'/source/activity/petgame')
    GRAPH.justify(0, petgame)

    for line in codecs.open(filename, encoding='utf-8', errors='replace'):
        line = line.strip()
        if line:
            parts = line.split(', ')
            user, frame_id, concept1, concept2 = parts
            frame = Frame.objects.get(id=int(frame_id))
            relation = frame.relation
            assertion = GRAPH.get_or_create_assertion(
                '/relation/'+relation.name,
                [u'/concept/zh_TW/'+concept1, u'/concept/zh_TW/'+concept2],
                {'dataset': 'conceptnet/zh_TW'}
            )
            print assertion['uri']

            raw = GRAPH.get_or_create_assertion(
                '/frame/zh_TW/'+frame.text,
                [u'/concept/zh_TW/'+concept1, u'/concept/zh_TW/'+concept2],
                {'dataset': 'conceptnet/zh_TW'}
            )
            print raw['uri']

            source_uri = u"/source/contributor/petgame/%s" % user
            source = GRAPH.get_or_create_node(source_uri)
            GRAPH.justify(0, source, weight=0.5)
            
            conjunction = GRAPH.get_or_create_conjunction([source, petgame])
            print conjunction['uri']
            GRAPH.justify(conjunction, raw)

if __name__ == '__main__':
    for filename in os.listdir('.'):
        if filename.startswith('conceptnet_zh_'):
            handle_file(filename)

