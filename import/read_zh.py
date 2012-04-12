from conceptnet.models import *
import os
import codecs
from conceptnet5.nodes import make_concept_uri
from conceptnet5.edges import make_edge, MultiWriter

sparse_pieces = []
for filename in os.listdir('.'):
    if filename.startswith('conceptnet_zh_'):
        writer = MultiWriter(filename.split('.')[0])
        for line in codecs.open(filename, encoding='utf-8', errors='replace'):
            line = line.strip()
            if line:
                parts = line.split(', ')
                user, frame_id, concept1, concept2 = parts
                frame = Frame.objects.get(id=int(frame_id))
                ftext = frame.text
                relation = frame.relation.name
                rel = '/r/'+relation

                surfaceText = frame.replace(u'{1}', u'[['+concept1+u']]').replace(u'{2}', u'[['+concept2+u']]')
                start = make_concept_uri(concept1, 'zh_TW')
                end = make_concept_uri(concept2, 'zh_TW')
                sources = ['/s/contributor/petgame/'+user, '/s/activity/ntt/petgame']
                edge = make_edge(rel, start, end, dataset='/d/conceptnet/4/zh',
                                 license='/l/CC/By', sources=sources,
                                 surfaceText=surfaceText, weight=1)
                writer.write(edge)
        writer.close()

