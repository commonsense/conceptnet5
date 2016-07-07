from __future__ import unicode_literals
from collections import defaultdict
from conceptnet5.uri import Licenses
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.semantic_web import (
    resource_name, parse_nquads
)


SOURCE = {'contributor': '/s/resource/wordnet/rdf/3.1'}
DATASET = '/d/wordnet/3.1'
WN20_URL = 'http://www.w3.org/2006/03/wn/wn20/instances/'

PARTS_OF_SPEECH = {
    'noun': 'n',
    'verb': 'v',
    'adjective': 'a',
    'adjectivesatellite': 'a',
    'adverb': 'r',
    'phrase': 'p'
}

REL_MAPPING = {
    'hypernym': ('IsA', '{0} is a type of {1}'),
    'part_meronym': ('PartOf', '{0} is a part of {1}'),
    'domain_category': ('HasContext', '{0} is used in the context of {1}'),
    'domain_region': ('HasContext', '{0} is used in the region of {1}'),
    'cause': ('Causes', '{0} causes {1}'),
    'action': ('UsedFor', '{0} is used for {1}'),
    'result': ('UsedFor', '{0} is used for {1}'),
    'beneficiary': ('UsedFor', '{0} is used for the benefit of {1}'),
    'location': ('AtLocation', '{0} is located in {1}'),
    'creator': ('CreatedBy', '{0} is created by {1}'),
    'entail': ('Entails', '{0} entails {1}'),
    'similar': ('SimilarTo', '{0} is similar to {1}'),
    'also': ('RelatedTo', '{0} is related to {1}'),
    'antonym': ('Antonym', '{0} is the opposite of {1}'),
    'derivation': ('DerivedFrom', 'The word "{0}" is derived from "{1}"'),
    'translation': ('~Synonym', '{0} is a translation of {1}'),

    # We may want some of these to be more specific, but it's hard to classify
    # them in terms of existing relations, and there aren't enough of them to
    # justify their own relations.
    'pertainym': ('RelatedTo', '{0} is related to {1}'),
    'agent': ('RelatedTo', '{0} is related to {1}'),
    'patient': ('RelatedTo', '{0} is related to {1}'),
    'theme': ('RelatedTo', '{0} is related to {1}'),
    'instrument': ('RelatedTo', '{0} is related to {1}'),
    'goal': ('RelatedTo', '{0} is related to {1}'),
    
    # Do we want a relation for verbs in the same VerbNet group?
}

# Some OMW languages come with Share-Alike restrictions that we should keep
# track of. Here's a list of them. This comes from the table at
# http://compling.hss.ntu.edu.sg/omw/, but the language codes are translated
# into BCP 47.

SHAREALIKE_LANGUAGES = [
    'ar', 'arb', 'nl', 'pt', 'ro', 'lt', 'sk', 'sl'
]


def label_sort_key(label):
    """
    A sort key that encourages more useful labels to come first, when we don't
    have a more solid basis to decide.

    * Prefer words starting with digits over words starting with letters:
      '101' is better than 'ci' or 'one hundred one'.
    * Prefer words ending with letters over words ending with digits:
      'hassium' is better than 'atomic number 108'.
    * Prefer lowercase words over capitalized ones: 'huge' is better than
      'Brobdingnagian'.
    * Prefer longer labels over shorter ones, as they're probably more
      specific: 'Paul Newman' is better than 'Newman'.
    * All else being equal, prefer the first label in alphabetical order.

    This is, fortunately, not the only way to choose labels. If a WordNet
    synset has a "sameAs" link pointing to a named synset in WordNet 2.0, we
    use that name, letting us use the label "United Kingdom" instead of
    "United Kingdom of Great Britain and Northern Ireland".

    However, we disregard the synset names for people, as they tend to be just
    the person's last name, and therefore are highly ambiguous in a way that
    won't be disambiguated by adding the category "person". For people, we
    apply this rule no matter what, choosing their longest name.
    """
    return (not label[0].isdigit(), label[-1].isdigit(), not label.islower(), -len(label), label)


def run_wordnet(input_file, output_file):
    out = MsgpackStreamWriter(output_file)

    synset_senses = defaultdict(list)
    sense_synsets = {}
    synset_labels = defaultdict(list)
    synset_canonical_labels = {}
    synset_categories = {}
    synset_domains = {}
    synset_glosses = {}
    synset_disambig = {}
    synset_uris = {}

    # First pass: find data about synsets
    quads = parse_nquads(open(input_file, encoding='utf-8'))
    for subj_dict, rel_dict, obj_dict, _graph in quads:
        if 'url' not in subj_dict or 'url' not in rel_dict:
            continue
        subj = subj_dict['url']
        rel = rel_dict['url']
        obj = obj_dict.get('url')
        objtext = obj_dict.get('text')

        relname = resource_name(rel)
        if relname == 'label':
            if obj_dict['lang'] == 'en':
                synset_labels[subj].append(objtext)
        elif relname == 'sameAs':
            if obj.startswith(WN20_URL):
                # If we have a link to RDF WordNet 2.0, the URL (URI? IRI?)
                # will contain a standardized label for this concept, which
                # we should use when we want to use this synset as the name of
                # a disambiguation category. RDF WordNet 3.1 assigns synsets
                # a number of labels in no particular order, making it hard to
                # determine from 3.1 alone what to name a category.
                objname = resource_name(obj)
                parts = objname.split('-')[1:-2]

                # Handle missing apostrophes
                label = '-'.join(parts).replace('_s_', "'s_").replace('_s-', "'s_").replace("s__", "s'_").replace("s_-", "s'-").replace('_', ' ')
                synset_canonical_labels[subj] = label

        elif relname == 'domain_category':
            synset_categories[subj] = obj
        elif relname == 'lexical_domain':
            target = resource_name(obj)
            if '.' in target:
                domain = target.split('.')[1]
                synset_domains[subj] = domain
        elif relname == 'gloss':
            synset_glosses[subj] = objtext
        elif relname == 'reference':
            lemma = resource_name(subj)
            synset = obj
            synset_senses[synset].append(lemma)
            sense_synsets[lemma] = synset

    used_labels = set(synset_canonical_labels.values())
    for synset, values in synset_labels.items():
        values.sort(key=lambda label: (label in used_labels,) + label_sort_key(label))
        if (
            synset not in synset_canonical_labels or
            synset_canonical_labels[synset][0].isupper() and synset_domains.get(synset) == 'person'
        ):
            label = values[0]
            synset_canonical_labels[synset] = label
            used_labels.add(label)

    for synset, labels in synset_labels.items():
        if synset in synset_categories:
            category_name = synset_canonical_labels[synset_categories[synset]]
        else:
            category_name = synset_domains.get(synset, None)
        synset_no_fragment = synset.split('#')[0]
        pos = synset_no_fragment[-1].lower()
        assert pos in 'nvarsp', synset
        if pos == 's':
            pos = 'a'
        elif pos == 'p':
            pos = '-'
        if category_name in ('pert', 'all', 'tops'):
            category_name = None
        synset_disambig[synset] = (pos, category_name)

        canon = synset_canonical_labels[synset]
        canon_uri = standardized_concept_uri('en', canon, pos, 'wn', category_name)
        synset_uris[synset] = canon_uri

        for label in labels:
            if label != canon:
                other_uri = standardized_concept_uri('en', label, pos, 'wn', category_name)
                rel_uri = '/r/Synonym'
                surface = '[[{0}]] is a synonym of [[{1}]]'.format(label, canon)
                edge = make_edge(
                    rel_uri, other_uri, canon_uri, dataset=DATASET, surfaceText=surface,
                    license=Licenses.cc_attribution, sources=[SOURCE], weight=2.0
                )
                out.write(edge)

    quads = parse_nquads(open(input_file, encoding='utf-8'))
    for subj_dict, rel_dict, obj_dict, _graph in quads:
        if 'url' not in subj_dict or 'url' not in rel_dict:
            continue
        subj = subj_dict['url']
        rel = rel_dict['url']
        obj = obj_dict.get('url')
        relname = resource_name(rel)
        if relname in REL_MAPPING:
            rel, frame = REL_MAPPING[relname]
            reversed_frame = False
            if rel.startswith('~'):
                rel = rel[1:]
                reversed_frame = True
            rel_uri = '/r/' + rel
            if obj is not None:
                obj_uri = synset_uris.get(obj)
                if obj not in synset_canonical_labels:
                    continue
                obj_label = synset_canonical_labels[obj]
            else:
                text = obj_dict['text']
                # Some WordNets use strings with "!" in them to indicate
                # out-of-band information, such as a missing translation
                if (not text) or '!' in text:
                    continue
                lang = obj_dict['lang']
                pos, sense = synset_disambig.get(subj, (None, None))
                obj_uri = standardized_concept_uri(lang, text, pos, 'wn', sense)
                obj_label = text

            if subj not in synset_uris or subj not in synset_canonical_labels:
                continue
            subj_uri = synset_uris[subj]
            subj_label = synset_canonical_labels[subj]
            license = Licenses.cc_attribution
            langcode = subj_uri.split('/')[2]
            if langcode in SHAREALIKE_LANGUAGES:
                license = Licenses.cc_sharealike

            if reversed_frame:
                subj_uri, obj_uri = obj_uri, subj_uri
                subj_label, obj_label = obj_label, subj_label

            surface = frame.format('[[%s]]' % subj_label, '[[%s]]' % obj_label)

            edge = make_edge(
                rel_uri, subj_uri, obj_uri, dataset=DATASET, surfaceText=surface,
                license=license, sources=[SOURCE], weight=2.0
            )
            out.write(edge)

    for wn_url in sorted(synset_uris):
        cn_uri = synset_uris[wn_url]
        edge = make_edge(
            '/r/ExternalURL', cn_uri, wn_url, dataset=DATASET,
            license=Licenses.cc_sharealike, sources=[SOURCE], weight=1.0
        )
        out.write(edge)

    out.close()


# Entry point for testing
handle_file = run_wordnet


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file', help="An .nt file containing WordNet RDF")
    parser.add_argument('output_file', help='Msgpack file to output to')
    args = parser.parse_args()
    run_wordnet(args.input_file, args.output_file)


if __name__ == '__main__':
    main()
