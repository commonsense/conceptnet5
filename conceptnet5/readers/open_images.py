from itertools import permutations

import pandas as pd
from collections import Counter

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.uri import Licenses

DATASET = '/d/open_images'
LICENSE = Licenses.cc_attribution
SOURCE = [{'contributor': '/s/resource/open_images/2017_11'}]

def get_labels_map(labels_descriptions):
    labels_frame = pd.read_csv(labels_descriptions, names=['LabelID', 'LabelName'])
    labels_frame['LabelName'] = labels_frame['LabelName'].apply(lambda row:
                                                                standardized_concept_uri('en', row))
    return pd.Series(labels_frame['LabelName'].values, index=labels_frame['LabelID']).to_dict()


def handle_files(inputs, labels_descriptions, output):
    out = MsgpackStreamWriter(output)
    labels_map = get_labels_map(labels_descriptions)
    all_pairs = []
    for input_filepath in inputs:
        frame = pd.read_csv(input_filepath)
        frame = frame[['ImageID', 'LabelName']]
        frame = frame.drop_duplicates()

        for key, group in frame.groupby('ImageID'):
            if len(group) > 1: # there are at least two objects in an image
                image_labels = [labels_map[label] for label in group['LabelName']]
                pairs = list(permutations(image_labels, 2))
                all_pairs.extend(pairs)
    counter = Counter(all_pairs)
    for rank, (pair, count) in enumerate(counter.most_common()):
        edge = make_edge(rel='/r/RelatedTo',
                         start=pair[0],
                         end=pair[1],
                         dataset=DATASET,
                         license=LICENSE,
                         sources=SOURCE)
        out.write(edge)
