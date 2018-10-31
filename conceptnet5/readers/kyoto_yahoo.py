"""
Import the data collected for ConceptNet 5 by Kyoto University & Yahoo
Japan Corporation, published in this paper by Naoki Otani et al.:

http://coling2016.okbqa.org/OKBQA201602.pdf
"""

from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.edges import make_edge
from conceptnet5.uri import Licenses

DATASET = '/d/conceptnet/5/ja'
SOURCE = '/s/activity/kyoto_yahoo'


def handle_file(input_filename, output_file):
    out = MsgpackStreamWriter(output_file)
    for line in open(input_filename, encoding='utf-8'):
        parts = line.rstrip('\n').split('\t')
        uri, start, rel, end, weight, source = parts
        if uri == 'uri':
            return
        
        edge = make_edge(
            rel=rel,
            start=start,
            end=end,
            dataset=DATASET,
            sources=[{'activity': SOURCE}],
            license=Licenses.cc_attribution,
            weight=float(weight) / 4
        )
        out.write(edge)
