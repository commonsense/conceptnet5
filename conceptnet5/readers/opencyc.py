"""
A reader for information from OpenCyc.

OpenCyc is distributed in RDF/XML format. In the raw data, we've used the
'rapper' command to convert it to n-quads. (All the quads are actually triples,
which is allowed. We just use .nq because it's a more modern format that isn't
limited to ASCII.)
"""

from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri, standardize_as_list
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.semantic_web import NTriplesReader, resource_name
from conceptnet5.language.token_utils import un_camel_case
from collections import defaultdict

SOURCE = {'contributor': '/s/resource/opencyc/2012'}
RDF_LABEL = 'http://www.w3.org/2000/01/rdf-schema#label'


def opencyc_edge(rel, start, end, start_text, end_text):
    """
    Get the ConceptNet representation of an OpenCyc edge.
    """
    return make_edge(
        rel=rel, start=start, end=end,
        dataset='/d/opencyc',
        license=Licenses.cc_attribution,
        sources=[SOURCE],
        weight=1.0,
        surfaceStart=start_text,
        surfaceEnd=end_text
    )


# These words tend to indicate Cyc internals that are presented the same way
# as facts about the external world.
BLACKLIST_WORDS = {
    'arg', 'arity', 'bugzilla', 'cbl', 'cblassign', 'centroid', 'cw', 'cyc',
    'fn', 'individual', 'mett', 'microtheory', 'mr', 'mt', 'opencyc', 'pcw',
    'temporally', 'type', 'union', 'underspecified', 'wn', 'wordnet'
}


def run_opencyc(input_file, output_file, sw_map_file):
    """
    Read an .nq file containing OpenCyc data, outputting a file of
    ConceptNet edges and a file of mappings between the Semantic Web and
    ConceptNet.
    """
    out = MsgpackStreamWriter(output_file)
    map_out = open(sw_map_file, 'w', encoding='utf-8')
    reader = NTriplesReader()

    labels = {}
    unlabels = defaultdict(set)

    # Read through the file once, finding all the "preferred labels". We will
    # use these as the surface texts for the nodes.
    for web_subj, web_rel, web_obj, objtag in reader.parse_file(input_file):
        if web_rel == RDF_LABEL:
            labels[web_subj] = web_obj
            unlabels[web_obj].add(web_subj)

    # Read through the file again and extract ConceptNet edges.
    for web_subj, web_rel, web_obj, objtag in reader.parse_file(input_file):
        rel_name = resource_name(web_rel)
        if rel_name == 'subClassOf' and objtag == 'URL' and web_subj in labels and web_obj in labels:
            subj_label = labels[web_subj]
            obj_label = labels[web_obj]
            subj_words = set(standardize_as_list(subj_label))
            obj_words = set(standardize_as_list(obj_label))
            if (subj_words & BLACKLIST_WORDS) or (obj_words & BLACKLIST_WORDS):
                continue
            if len(subj_words) > 4 or len(obj_words) > 4:
                continue

            subj_uri = cyc_to_conceptnet_uri(labels, unlabels, web_subj)
            obj_uri = cyc_to_conceptnet_uri(labels, unlabels, web_obj)
            out.write(opencyc_edge('/r/IsA', subj_uri, obj_uri, subj_label, obj_label))
            map_out.write('{}\t{}\n'.format(web_subj, subj_uri))
            map_out.write('{}\t{}\n'.format(web_obj, obj_uri))
        elif rel_name == 'sameAs' and web_subj in labels and web_obj.startswith('http://umbel.org/'):
            subj_label = labels[web_subj]
            subj_uri = standardized_concept_uri('en', subj_label)
            map_out.write('{}\t{}\n'.format(web_obj, subj_uri))


def cyc_to_conceptnet_uri(labels, unlabels, uri):
    label = labels[uri]
    if len(unlabels[label]) >= 2:
        disambig = un_camel_case(resource_name(uri))
        if standardize_as_list(disambig) != standardize_as_list(label):
            return standardized_concept_uri('en', label, 'n', 'opencyc', disambig)
    return standardized_concept_uri('en', label, 'n', 'opencyc')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help="An N-triples or N-quads file of input")
    parser.add_argument('output', help='msgpack file to output to')
    parser.add_argument('sw_map', help='A tab-separated file of Semantic Web equivalences to write')
    args = parser.parse_args()
    run_opencyc(args.input, args.output, args.sw_map)

if __name__ == '__main__':
    main()
