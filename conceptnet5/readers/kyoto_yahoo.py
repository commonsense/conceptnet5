"""
Import the data collected for ConceptNet 5 by Kyoto University & Yahoo
Japan Corporation, published in this paper by Naoki Otani et al.:

http://coling2016.okbqa.org/OKBQA201602.pdf
"""

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.uri import Licenses

# Assign a unique dataset and source to this data
DATASET = '/d/kyoto_yahoo'
SOURCE = '/s/activity/kyoto_yahoo'


WEIGHT_TABLE = {'3': 0.5, '4': 1.0, '5': 2.0}


def handle_file(input_filename, output_file):
    out = MsgpackStreamWriter(output_file)
    for line in open(input_filename, encoding='utf-8'):
        parts = line.rstrip('\n').split('\t')
        uri, start, rel, end, weight, source = parts
        if uri == 'uri':
            continue

        edge = make_edge(
            rel=rel,
            start=start,
            end=end,
            dataset=DATASET,
            sources=[{'activity': SOURCE}],
            license=Licenses.cc_attribution,
            weight=WEIGHT_TABLE[weight],
        )
        out.write(edge)
