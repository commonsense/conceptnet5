from __future__ import unicode_literals
from collections import defaultdict
from conceptnet5.uri import join_uri
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.semantic_web import NTriplesReader, NTriplesWriter, resource_name, full_conceptnet_url
import re
import os


SOURCE = '/s/wordnet/3.0'

PARTS_OF_SPEECH = {
    'noun': 'n',
    'verb': 'v',
    'adjective': 'a',
    'adjectivesatellite': 'a',
    'adverb': 'r',
}

REL_MAPPING = {
    'attribute': 'Attribute',
    'causes': 'Causes',
    'classifiedByRegion': 'HasContext',
    'classifiedByUsage': 'HasContext',
    'classifiedByTopic': 'HasContext',
    'entails': 'Entails',
    'hyponymOf': 'IsA',
    'instanceOf': 'InstanceOf',
    'memberMeronymOf': 'MemberOf',
    'partMeronymOf': 'PartOf',
    'sameVerbGroupAs': 'SimilarTo',
    'similarTo': 'SimilarTo',
    'substanceMeronymOf': '~MadeOf',
    'antonymOf': 'Antonym',
    'derivationallyRelated': '~DerivedFrom',
    'pertainsTo': 'PertainsTo',
    'seeAlso': 'RelatedTo',
}


def run_wordnet(input_dir, output_file, sw_map_file):
    out = MsgpackStreamWriter(output_file)
    map_out = NTriplesWriter(sw_map_file)
    reader = NTriplesReader()

    synset_senses = defaultdict(list)
    sense_synsets = {}

    labels = {}
    glossary = {}
    concept_map = {}
    sense_to_synset = {}

    # Parse lines such as:
    #   wn30:synset-Aeolian-noun-2 rdfs:label "Aeolian"@en-us .
    for subj, rel, obj, objtag in reader.parse_file(os.path.join(input_dir, 'wordnet-synset.ttl')):
        if resource_name(rel) == 'label':
            # Everything in WordNet is in English
            assert objtag == 'en'
            labels[subj] = obj

    for subj, rel, obj, objtag in reader.parse_file(os.path.join(input_dir, 'wordnet-glossary.ttl')):
        if resource_name(rel) == 'gloss':
            assert objtag == 'en'

            # Take the definition up to the first semicolon
            text = obj.split(';')[0]

            # Remove introductory phrases with a colon
            text = text.split(': ', 1)[-1]

            # Remove parenthesized expressions
            while True:
                newtext = re.sub(r'\(.+?\) ?', '', text).strip()
                if newtext == text or newtext == '':
                    break
                else:
                    text = newtext

            glossary[subj] = text.replace('/', '_')

    # Get the list of word senses in each synset, and make a bidirectional mapping.
    #
    # Example line:
    #   wn30:synset-Aeolian-noun-2 wn20schema:containsWordSense wn30:wordsense-Aeolian-noun-2 .
    for subj, rel, obj, objtag in reader.parse_file(os.path.join(input_dir, 'full/wordnet-wordsense-synset-relations.ttl')):
        if resource_name(rel) == 'containsWordSense':
            synset_senses[subj].append(obj)
            sense_synsets[obj] = subj

    # Assign every synset to a disambiguated concept.
    for synset in synset_senses:
        synset_name = labels[synset]
        synset_pos = synset.split('-')[-2]
        pos = PARTS_OF_SPEECH[synset_pos]
        disambig = glossary[synset]

        concept = standardized_concept_uri('en', synset_name, pos, disambig)
        concept_map[synset] = concept

    # Map senses to their synsets.
    for sense, synset in sense_synsets.items():
        sense_to_synset[sense] = synset

    for filename in (
        'wordnet-attribute.ttl', 'wordnet-causes.ttl',
        'wordnet-classifiedby.ttl', 'wordnet-entailment.ttl',
        'wordnet-hyponym.ttl', 'wordnet-instances.ttl',
        'wordnet-membermeronym.ttl', 'wordnet-partmeronym.ttl',
        'wordnet-sameverbgroupas.ttl', 'wordnet-similarity.ttl',
        'wordnet-substancemeronym.ttl', 'full/wordnet-antonym.ttl',
        'full/wordnet-derivationallyrelated.ttl',
        'full/wordnet-participleof.ttl',
        'full/wordnet-pertainsto.ttl',
        'full/wordnet-seealso.ttl'
    ):
        filepath = os.path.join(input_dir, filename)
        if os.path.exists(filepath):
            for web_subj, web_rel, web_obj, objtag in reader.parse_file(filepath):
                # If this relation involves word senses, map them to their synsets
                # first.
                if web_subj in sense_to_synset:
                    web_subj = sense_to_synset[web_subj]
                if web_obj in sense_to_synset:
                    web_obj = sense_to_synset[web_obj]
                subj = concept_map[web_subj]
                obj = concept_map[web_obj]
                pred_label = resource_name(web_rel)
                if pred_label in REL_MAPPING:
                    mapped_rel = REL_MAPPING[pred_label]

                    # Handle WordNet relations that are the reverse of ConceptNet
                    # relations. Change the word 'meronym' to 'holonym' if
                    # necessary.
                    if mapped_rel.startswith('~'):
                        subj, obj = obj, subj
                        web_subj, web_obj = web_obj, web_subj
                        web_rel = web_rel.replace('meronym', 'holonym')
                        mapped_rel = mapped_rel[1:]
                    rel = join_uri('r', mapped_rel)
                else:
                    rel = join_uri('r', 'wordnet', pred_label)

                map_out.write_link(web_rel, full_conceptnet_url(rel))
                map_out.write_link(web_subj, full_conceptnet_url(subj))
                map_out.write_link(web_obj, full_conceptnet_url(obj))
                edge = make_edge(
                    rel, subj, obj, dataset='/d/wordnet/3.0',
                    license='/l/CC/By', sources=SOURCE, weight=2.0
                )
                out.write(edge)


# Entry point for testing
handle_file = run_wordnet


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help="Directory containing WordNet files")
    parser.add_argument('output', help='Msgpack file to output to')
    parser.add_argument('sw_map', help='A .nt file of Semantic Web equivalences')
    args = parser.parse_args()
    run_wordnet(args.input_dir, args.output, args.sw_map)

if __name__ == '__main__':
    main()
