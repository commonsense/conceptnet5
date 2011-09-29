from conceptnet.models import *
from conceptnet5.graph import *
import divisi2
import os
import codecs

def handle_file(filename):
    for line in codecs.open(filename, encoding='utf-8', errors='replace'):
        line = line.strip()
        if line:
            parts = line.split(', ')
            user, frame_id, concept1, concept2 = parts
            frame = Frame.objects.get(id=int(frame_id))
            relation = frame.relation

            assertion = u"/assertion/_/relation/%s/_/concept/zh_TW/%s/_/concept/zh_TW/%s" % (relation.name, concept1, concept2)
            print encode_uri(assertion)

            raw = u"/assertion/_/frame/%s/_/text/zh_TW/%s/_/text/zh_TW/%s" % (frame.text, concept1, concept2)
            print encode_uri(raw)

            # TODO: have raw justify assertion, have the 

for filename in os.listdir('.'):
    if filename.startswith('conceptnet_zh_'):
        handle_file(filename)

