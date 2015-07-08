# coding: utf-8
from __future__ import unicode_literals
"""
A reader for information from Umbel, an RDF transformation of OpenCyc.

Umbel is distributed in formats such as RDF/XML and N3, all of which are
inconvenient to work with. However, external tools can convert an N3 file
into an N-Triples file, which this code is able to understand.
"""

from conceptnet5.language.token_utils import un_camel_case
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri, standardized_concept_name, standardize_text
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.semantic_web import NTriplesReader, NTriplesWriter, resource_name, full_conceptnet_url
from conceptnet5.readers.dbpedia import translate_dbpedia_url
from collections import defaultdict
import os


# As far as I can tell, Umbel doesn't have version identifiers. I use the year
# the resource seems to have been created as a version.
SOURCE = '/s/umbel/2013'
LINK_SOURCE = '/s/dbpedia/3.9/umbel'

# OpenCyc really only has things that ConceptNet would call IsA relationships.
# Because our policy is not to try to make the type-token distinction, this
# includes both types and subclasses.
#
# REL_MAPPING maps the UMBEL link type to a ConceptNet relation and the
# natural-language frame that should be filled in.
REL_MAPPING = {
    'type': ('/r/IsA', '[[%s]] is an instance of [[%s]]'),
    'subClassOf': ('/r/IsA', '[[%s]] is a subclass of [[%s]]')
}
SYN_FRAME = '[[%s]] is a synonym of [[%s]]'


def umbel_edge(rel, start, end, surface, source):
    """
    Get the ConceptNet representation of an UMBEL edge.
    """
    return make_edge(
        rel=rel, start=start, end=end,
        dataset='/d/umbel',
        license=Licenses.cc_attribution,
        sources=[source],
        weight=1.0,
        surfaceText=surface
    )


IGNORED_NODES = set([
    'PersonWithOccupation', 'EukaryoticCell'
])
IGNORED_WORDS = set([
    'will', 'have', 'has', 'had', 'cw', 'pcw'
])

def acceptable_node(url):
    return not (url.endswith('Type') or url.endswith('Concept')
                or resource_name(url) in IGNORED_NODES)


def run_umbel(input_dir, output_file, sw_map_file):
    """
    Read N-Triples files containing Umbel data, outputting a file of
    ConceptNet edges and a file of mappings between the Semantic Web and
    ConceptNet.
    """
    out = MsgpackStreamWriter(output_file)
    map_out = NTriplesWriter(sw_map_file)
    reader = NTriplesReader()

    labels = {}
    label_sets = defaultdict(set)

    # There are two files we want to parse:
    # - umbel.nt, a transformation of umbel.n3, which is available from
    #   https://github.com/structureddynamics/UMBEL/.
    # - umbel_links.nt, distributed with DBPedia 3.9.
    #
    # We parse them both in this file so that umbel_links can reuse the
    # concept names extracted from umbel.nt.
    main_file = os.path.join(input_dir, 'umbel.nt')
    dbpedia_link_file = os.path.join(input_dir, 'umbel_links.nt')

    # Read through umbel.nt once, finding all the "preferred labels". We will
    # use these as the surface texts for the nodes.
    for web_subj, web_rel, web_obj, objtag in reader.parse_file(main_file):
        if resource_name(web_rel) == 'prefLabel':
            # 'CW' and 'PCW' are Cyc jargon for 'conceptual works'. If a node
            # cannot be described except as a CW, we're probably not
            # interested in it.
            if 'CW' not in web_obj.split() and 'PCW' not in web_obj.split():
                labels[web_subj] = web_obj
        if resource_name(web_rel).endswith('Label'):
            text = standardize_text(web_obj)
            label_sets[text].add(web_subj)

    # Read through umbel.nt again and extract ConceptNet edges.
    for web_subj, web_rel, web_obj, objtag in reader.parse_file(main_file):
        if objtag == 'URL' and acceptable_node(web_obj) and acceptable_node(web_subj):
            # Only use nodes for which we've seen preferred labels.
            # (This skips some anonymous OWL-cruft nodes.)
            if web_subj in labels and web_obj in labels:
                subj_uri = standardized_concept_uri('en', labels[web_subj])
                obj_uri = standardized_concept_uri('en', labels[web_obj])
                rel_name = resource_name(web_rel)
                # Check if this is a relation we want to handle.
                if rel_name in REL_MAPPING:
                    # Write the ConceptNet edges and the mappings to Semantic Web URLs.
                    rel_uri, frame = REL_MAPPING[rel_name]
                    surface = frame % (labels[web_subj], labels[web_obj])
                    out.write(umbel_edge(rel_uri, subj_uri, obj_uri, surface, SOURCE))
                    map_out.write_link(web_rel, full_conceptnet_url(rel_uri))
                    map_out.write_link(web_subj, full_conceptnet_url(subj_uri))
                    map_out.write_link(web_obj, full_conceptnet_url(obj_uri))

        # altLabel relations assign different texts to the same node. We'll
        # represent those in ConceptNet with Synonym relations.
        elif web_rel.endswith('altLabel'):
            # Make sure we know what's being labeled.
            if web_subj in labels:
                name = web_obj
                words = name.split(' ')
                if standardized_concept_name('en', name) != standardized_concept_name('en', labels[web_subj]):
                    if not set(words) & IGNORED_WORDS:
                        main_label = standardized_concept_uri('en', labels[web_subj])
                        name_text = standardize_text(name)
                        if len(label_sets[name_text]) >= 2 or len(name_text) <= 3:
                            disambig = un_camel_case(resource_name(web_subj))

                            # Cyc does not distinguish texts by their part of speech, so use
                            # '_' as the part of speech symbol.
                            alt_label = standardized_concept_uri('en', name, '_', disambig)
                        else:
                            alt_label = standardized_concept_uri('en', name)
                        surface = SYN_FRAME % (name, labels[web_subj])
                        out.write(umbel_edge('/r/Synonym', alt_label, main_label, surface, SOURCE))

    for web_subj, web_rel, web_obj, objtag in reader.parse_file(dbpedia_link_file):
        if objtag == 'URL' and acceptable_node(web_obj) and acceptable_node(web_subj):
            if web_obj in labels:
                subj_label = resource_name(web_subj).replace('_', ' ')
                subj_uri = translate_dbpedia_url(web_subj)
                obj_label = labels[web_obj]
                obj_uri = standardized_concept_uri('en', obj_label)
                rel_name = resource_name(web_rel)
                if rel_name in REL_MAPPING:
                    rel_uri, frame = REL_MAPPING[rel_name]
                    surface = frame % (subj_label, obj_label)
                    out.write(umbel_edge(rel_uri, subj_uri, obj_uri, surface, LINK_SOURCE))
                    map_out.write_link(web_rel, full_conceptnet_url(rel_uri))
                    map_out.write_link(web_subj, full_conceptnet_url(subj_uri))
                    map_out.write_link(web_obj, full_conceptnet_url(obj_uri))


# Entry point for testing
handle_file = run_umbel


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help="Directory containing .nt files of input")
    parser.add_argument('output', help='msgpack file to output to')
    parser.add_argument('sw_map', help='A .nt file of Semantic Web equivalences')
    args = parser.parse_args()
    run_umbel(args.input_dir, args.output, args.sw_map)

if __name__ == '__main__':
    main()
