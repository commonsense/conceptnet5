import os
import codecs
import sys
import json
from collections import defaultdict
from conceptnet5.nodes import make_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.whereami import get_project_filename

FRAME_DATA = json.load(
    codecs.open(get_project_filename('data/info/zh_frames.json'))
)


def handle_raw_assertion(line):
    if not line:
        return
    parts = line.split(', ')
    user, frame_id, concept1, concept2 = parts
    fdata = FRAME_DATA[frame_id]
    ftext = fdata['text']
    rel = fdata['relation']

    surfaceText = ftext.replace(u'{1}', u'[['+concept1+u']]').replace(u'{2}', u'[['+concept2+u']]')
    start = make_concept_uri(concept1, 'zh_TW')
    end = make_concept_uri(concept2, 'zh_TW')
    sources = ['/s/activity/ptt/petgame', '/s/contributor/petgame/' + user]
    edge = make_edge(rel, start, end, dataset='/d/conceptnet/4/zh',
                     license='/l/CC/By', sources=sources,
                     surfaceText=surfaceText, weight=1)
    yield json.dumps(edge, ensure_ascii=False)

if __name__ == '__main__':
    from conceptnet5.readers import transform_stream
    transform_stream(handle_raw_assertion)

