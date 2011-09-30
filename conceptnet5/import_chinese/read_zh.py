from conceptnet.models import Frame
from conceptnet5.graph import get_graph
import divisi2
import os
import codecs

GRAPH = get_graph()

def handle_file(filename):
    petgame = GRAPH.get_or_create_node(u'/source/activity/petgame')
    for line in codecs.open(filename, encoding='utf-8', errors='replace'):
        line = line.strip()
        if line:
            parts = line.split(', ')
            user, frame_id, concept1, concept2 = parts
            frame = Frame.objects.get(id=int(frame_id))
            relation = frame.relation

            assertion_uri = u"/assertion/_/relation/%s/_/concept/zh_TW/%s/_/concept/zh_TW/%s" % (relation.name, concept1, concept2)
            print assertion_uri
            assertion = GRAPH.get_or_create_node(assertion_uri)

            raw_uri = u"/assertion/_/frame/%s/_/concept/zh_TW/%s/_/concept/zh_TW/%s" % (frame.text, concept1, concept2)
            raw = GRAPH.get_or_create_node(raw_uri)
            GRAPH.derive_normalized(raw, assertion)

            source_uri = u"/source/contributor/petgame/%s" % user
            source = GRAPH.get_or_create_node(source_uri)
            
            conjunction = GRAPH.get_or_create_conjunction([source, petgame])
            print conjunction['uri']
            GRAPH.justify(conjunction, raw)

for filename in os.listdir('.'):
    if filename.startswith('conceptnet_zh_'):
        handle_file(filename)

