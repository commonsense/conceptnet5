from itertools import chain
from collections import defaultdict
from conceptnet5.graph import JSONWriterGraph
import re

mapping = {}
labels = {}
prefixes = {}
glossary = {}
synset_senses = defaultdict(list)
sense_synsets = {}

parts_of_speech = {
    'noun': 'n',
    'verb': 'v',
    'adjective': 'a',
    'adjectivesatellite': 'a',
    'adverb': 'r',
}

rel_mapping = {
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

def resolve_prefix(entry):
    prefix, name = entry.split(':')
    return prefixes[prefix] + name

def handle_line(line):
    """
    Get the (subj, obj, pred) parts of a line, unless it's a blank line
    or a prefix definition, in which case return None.
    """
    line = line.decode('utf-8').strip()
    if not line:
        return None
    parts = line.split(None, 2)
    if parts[0] == '@prefix':
        prefix = parts[1].strip(': ')
        value = parts[2].strip('<>. ')
        prefixes[prefix] = value
        return None
    return parts[0], parts[1], parts[2].strip('. ')

# First, get the human-readable label and gloss for every synset.
for line in chain(
    open('wordnet-synset.ttl'),
    open('full/wordnet-wordsensesandwords.ttl'),
    open('wordnet-glossary.ttl')
):
    parts = handle_line(line)
    if parts is None:
        continue
    if parts[1] == 'rdfs:label':
        subj = resolve_prefix(parts[0])
        obj = parts[2].split('"')[1]
        labels[subj] = obj
    elif parts[1] == 'wn20schema:gloss':
        subj = resolve_prefix(parts[0])
        obj = parts[2].split('"')[1]
        glossary[subj] = obj.split(';')[0]
        while '(' in glossary[subj] and ')' in glossary[subj]:
            glossary[subj] = re.sub(r"\([^)]+\) ?", r"", glossary[subj])

# Get the list of word senses in each synset, and make a bidirectional mapping.
for line in open('full/wordnet-wordsense-synset-relations.ttl'):
    parts = handle_line(line)
    if parts is None:
        continue
    if parts[1] == 'wn20schema:containsWordSense':
        subj = resolve_prefix(parts[0])
        obj = resolve_prefix(parts[2].strip('. '))
        synset_senses[subj].append(obj)
        sense_synsets[obj] = subj

# Assign every synset a disambiguation name, which is its gloss.
for synset in synset_senses:
    senses = sorted(synset_senses[synset])
    synset_name = labels[synset]
    synset_pos = synset.split('-')[-2]
    pos = parts_of_speech[synset_pos]
    disambig = glossary[synset]
    node = "/concept/en/%s/%s/%s" % (synset_name, pos, disambig)
    if synset not in mapping:
        mapping[synset] = node

# Map senses to the same nodes.
for sense, synset in sense_synsets.items():
    mapping[sense] = mapping[synset]

GRAPH = JSONWriterGraph('../json_data/wordnet')
source = GRAPH.get_or_create_node('/source/wordnet/3.0')
GRAPH.justify('/', source, 10)

for line in chain(
    open('wordnet-attribute.ttl'),
    open('wordnet-causes.ttl'),
    open('wordnet-classifiedby.ttl'),
    open('wordnet-entailment.ttl'),
    open('wordnet-hyponym.ttl'),
    open('wordnet-instances.ttl'),
    open('wordnet-membermeronym.ttl'),
    open('wordnet-partmeronym.ttl'),
    open('wordnet-sameverbgroupas.ttl'),
    open('wordnet-similarity.ttl'),
    open('wordnet-substancemeronym.ttl'),
    open('full/wordnet-antonym.ttl'),
    open('full/wordnet-derivationallyrelated.ttl'),
    open('full/wordnet-participleof.ttl'),
    open('full/wordnet-pertainsto.ttl'),
    open('full/wordnet-seealso.ttl'),
):
    parts = handle_line(line)
    if parts is None:
        continue
    web_subj = resolve_prefix(parts[0])
    web_rel = resolve_prefix(parts[1])
    web_obj = resolve_prefix(parts[2])
    subj = mapping[web_subj]
    obj = mapping[web_obj]
    pred_label = parts[1].split(':')[-1]
    if pred_label in rel_mapping:
        mapped = rel_mapping[pred_label]
        if mapped.startswith('~'):
            subj, obj = obj, subj
            web_subj, web_obj = web_obj, web_subj
            web_rel = web_rel.replace('meronym', 'holonym')
            mapped = mapped[1:]
        pred = '/relation/'+mapped
    else:
        pred = '/relation/'+pred_label

    raw = GRAPH.get_or_create_assertion(
        GRAPH.get_or_create_web_concept(web_rel),
        [GRAPH.get_or_create_web_concept(web_subj), GRAPH.get_or_create_web_concept(web_obj)],
        {'dataset': 'wordnet/en/3.0', 'license': 'CC-By', 'normalized': False}
    )
    assertion = GRAPH.get_or_create_assertion(
        GRAPH.get_or_create_node(pred),
        [GRAPH.get_or_create_node(subj), GRAPH.get_or_create_node(obj)],
        {'dataset': 'wordnet/en/3.0', 'license': 'CC-By', 'normalized': True}
    )
    GRAPH.justify(source, raw)
    GRAPH.derive_normalized(raw, assertion)
    print assertion

