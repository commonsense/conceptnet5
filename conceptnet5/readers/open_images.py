from itertools import permutations

import pandas as pd
import numpy as np
from collections import Counter

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.uri import Licenses

DATASET = '/d/open_images'
LICENSE = Licenses.cc_attribution
SOURCE = [{'contributor': '/s/resource/open_images/2017_11'}]


def get_label_id_to_name_map(labels_descriptions):
    """
    Read in a mapping between label ids and their names. Convert the names to uris.
    """
    labels_frame = pd.read_csv(labels_descriptions, names=['LabelID', 'LabelName'])
    labels_frame['LabelName'] = labels_frame['LabelName'].apply(lambda row:
                                                                standardized_concept_uri('en', row))
    return pd.Series(labels_frame['LabelName'].values, index=labels_frame['LabelID']).to_dict()


def handle_files(inputs, labels_descriptions, output):
    """
    Read in OpenImages annotations and create edges for concepts that appeared in the same picture.
    """
    out = MsgpackStreamWriter(output)
    label_id_to_name = get_label_id_to_name_map(labels_descriptions)
    all_pairs = []
    for input_filepath in inputs:
        frame = pd.read_csv(input_filepath)
        frame = frame[['ImageID', 'LabelName']]
        frame = frame.drop_duplicates()
        frame['LabelName'] = frame['LabelName'].apply(lambda label_id: label_id_to_name[label_id])

        for key, group in frame.groupby('ImageID'):
            if len(group) > 1:
                pairs = list(permutations(group['LabelName'], 2))
                all_pairs.extend(pairs)
    counter = Counter(all_pairs)

    # Use a normalized log count of a pair as its weight, if it's larger than 0.2
    counts = [count for pair, count in counter.most_common()]
    log_counts = [np.log(count) for count in counts]
    max_count = max(log_counts)
    min_count = min(log_counts)
    norm = max_count - min_count

    for pair, count in counter.most_common():
        weight = (np.log(count) - min_count) / norm
        edge = make_edge(rel='/r/LocatedNear',
                         start=pair[0],
                         end=pair[1],
                         dataset=DATASET,
                         license=LICENSE,
                         sources=SOURCE,
                         weight=max(weight, 0.2))
        out.write(edge)
