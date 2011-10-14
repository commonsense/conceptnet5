from itertools import chain
from collections import defaultdict
import re

mapping = {}
labels = {}
prefixes = {}
glossary = {}
synset_senses = defaultdict(list)
parts_of_speech = {
    'noun': 'n',
    'verb': 'v',
    'adjective': 'a',
    'adjectivesatellite': 'a',
    'adverb': 'r',
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
            print glossary[subj]
            glossary[subj] = re.sub(r"\([^)]+\) ?", r"", glossary[subj])
            print glossary[subj]

# Get the list of word senses in each synset.
for line in open('full/wordnet-wordsense-synset-relations.ttl'):
    parts = handle_line(line)
    if parts is None:
        continue
    if parts[1] == 'wn20schema:containsWordSense':
        subj = resolve_prefix(parts[0])
        obj = resolve_prefix(parts[2].strip('. '))
        synset_senses[subj].append(obj)

# Assign every synset a disambiguation name, which is its gloss.
for synset in synset_senses:
    senses = sorted(synset_senses[synset])
    synset_name = labels[synset]
    synset_pos = synset.split('-')[-2]
    pos = parts_of_speech[synset_pos]
    disambig = glossary[synset]
    node = "/concept/en/%s/%s/%s" % (synset_name, pos, disambig)
    if synset not in mapping:
        print 'GLOSS:', 
        mapping[synset] = node
        print synset, node

