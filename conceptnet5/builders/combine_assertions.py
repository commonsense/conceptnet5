import codecs
from conceptnet5.edges import make_edge, MultiWriter
from conceptnet5.nodes import make_disjunction_uri
from collections import defaultdict
from multiprocessing import Process
import time
import os
import sys
import json
import math

N = 100
CURRENT_DIR = os.getcwd()

def combine_assertions(csv_filename, out_filename, dataset, license):
    current_uri = None
    current_data = {}
    current_surface = None
    current_weight = 0.
    current_sources = []
    out = codecs.open(out_filename, 'w', encoding='utf-8')
    for line in codecs.open(csv_filename, encoding='utf-8'):
        uri, rel, start, end, context, weight, source_uri, id, this_dataset, surface = line.split('\t')[:10]
        weight = float(weight)
        surface = surface.strip()
        if uri == 'uri':
            continue
        if uri == current_uri:
            current_weight += weight
            current_sources.append(source_uri)
            if (current_surface is None) and surface:
                current_surface = surface
        else:
            if current_uri is not None:
                output_assertion(out,
                    dataset=dataset, license=license,
                    sources=current_sources,
                    surfaceText=current_surface,
                    weight=current_weight,
                    uri=current_uri,
                    **current_data
                )
            current_uri = uri
            current_data = {
                'rel': rel,
                'start': start,
                'end': end
            }
            current_weight = weight
            current_sources = [source_uri]
            current_surface = surface or None
    
    output_assertion(out,
        rel=rel, start=start, end=end,
        dataset=dataset, license=license,
        sources=current_sources,
        surfaceText=current_surface,
        weight=current_weight,
        uri=current_uri
    )
    out.close()

def output_assertion(out, **kwargs):
    uri = kwargs.pop('uri')
    source_tree = make_disjunction_uri(set(kwargs.pop('sources')))
    assertion = make_edge(sources=source_tree, **kwargs)
    current_weight = assertion['weight']
    log_weight = math.log(max(1, current_weight + 1)) / math.log(2)
    assertion['weight'] = log_weight
    
    assert assertion['uri'] == uri, (assertion['uri'], uri)
    line = json.dumps(assertion, ensure_ascii=False)
    print >> out, line

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='csv file of input')
    parser.add_argument('output', help='jsons file to output to')
    parser.add_argument('-d', '--dataset',
        help='URI of the dataset to build, such as /d/conceptnet/5/combined-core'
    )
    parser.add_argument('-l', '--license',
        help='URI of the license to use, such as /l/CC/By-SA'
    )
    args = parser.parse_args()
    combine_assertions(args.input, args.output, args.dataset, args.license)

