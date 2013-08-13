"""
This script reads the conceptnet4 data out of the flat files in raw_data
and builds conceptnet5 edges from the data.  
"""

import os
import codecs
import sys
import re
import argparse
import json

from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri, make_concept_uri


LICENSE = '/l/CC/By'

# bedume is a prolific OMCS contributor who seemed to go off the rails at some
# point, adding lots of highly correlated nonsense assertions. We need to
# filter them out without losing his informative statements.

BEDUME_FLAGGED_CONCEPTS = [
  'cute', 'lose', 'sew', 'brat', 'work', 'sex', 'shop', 'drive to work',
  'type', 'in jail', 'jog in park', 'wash his car', 'poor', 'pull weed',
  'dance', 'sleep', 'pout', 'rake leave', 'wash her car', 'chop wood',
  'write book', 'shout', 'take out garbage', 'it', 'cry', 'run', 'cook',
  'late', 'happy', 'eat', 'afraid', 'vote', 'thief', 'shovel snow',
  'drink', 'drunk', 'watch tv', 'nut', 'early', 'well', 'ill', 'jog',
  'dead', 'naked', 'play card', 'sick', 'paint', 'read', 'hunter',
  'play monopoly', 'build new house', 'ride horse', 'play in football game',
  'make love', 'knit', 'go to take vacation', 'fish', 'go to dentist',
  'go to store', 'go to airport', 'go to go to store', 'kid', 'computer',
  'stew', 'take walk', 'tire', 'new computer', 'horn', 'serve mealfish',
  'potatoe shed', 'hunt', 'crazy', 'buy new car', 'laugh', 'intoxicated',
  'intoxicate', 'eat hamburger', 'wok'
]
BEDUME_FLAGGED_PLACES = [
  'alaska', 'kansa', 'utah', 'austria', 'delaware', 'pennsylvania', 
  'italy', 'cuba', 'norway', 'idaho', 'france', 'utha', 'mexico',
  'connecticut', 'massachusetts', 'montana', 'wyoming', 'every state',
  'new york', 'maine', 'suface of moon', 'germany', 'nebraska',
  'finland', 'louisiana', 'belgium', 'morrocco', 'ireland', 'ceylon',
  'california', 'oregon', 'florida', 'uraguay', 'egypt', 'maryland',
  'washington', 'morocco', 'south dakota', 'tuscon', 'panama', 'alberta',
  'arizona', 'texas', 'new jersey', 'colorado', 'jamaica', 'vermont',
  'nevada', 'delawere', 'hawaii', 'minnesota', 'tuscony', 'costa rica',
  'south dakato', 'china', 'argentina', 'venazuela', 'honduras',
  'opera', 'wisconsin', 'great britain',
]

def can_skip(parts_dict):
    lang = parts_dict['lang']
    if lang.startswith('zh'):
        return True
    if lang == 'ja':
        return True
    if parts_dict["goodness"] < 1:
        return True

    if 'rubycommons' in parts_dict["activity"]: 
        return True
    return False

def build_frame_text(parts_dict):
    frame_text = parts_dict["frame_text"]
    # Mark frames where {2} precedes {1} with an asterisk.
    if frame_text.find('{1}') > frame_text.find('{2}'):
        frame_text = '*' + frame_text
    polarity = parts_dict["polarity"]
    if polarity > 0:
        frame_text = frame_text.replace('{%}', '')
    else:
        frame_text = frame_text.replace('{%}', 'not')
    frame_text = frame_text.replace('{1}', '[[%s]]' % parts_dict["startText"]).replace('{2}', '[[%s]]' % parts_dict["endText"])
    return frame_text

def build_relation(parts_dict):
    relname = parts_dict["relname"]
    polarity = polarity = parts_dict["polarity"]
    if relname == 'ConceptuallyRelatedTo':
        relname = 'RelatedTo'

    if polarity > 0:
        relation = normalize_uri('/r/'+relname)
    else:
        relation = normalize_uri('/r/Not'+relname)

    return relation

def build_start(parts_dict):
    lang = parts_dict['lang']
    startText = parts_dict["startText"]
    start = make_concept_uri(startText, lang)
    return start

def build_end(parts_dict):
    lang = parts_dict['lang']
    endText = parts_dict["endText"]
    end = make_concept_uri(endText, lang)
    return end

def build_data_set(parts_dict):
    lang = parts_dict['lang']
    dataset = normalize_uri('/d/conceptnet/4/'+lang)
    return dataset

def build_sources(parts_dict):
    activity = parts_dict["activity"]

    creator_node = normalize_uri(u'/s/contributor/omcs/'+parts_dict["creator"])
    activity_node = normalize_uri(u'/s/activity/omcs/'+activity)
    sources = [([creator_node, activity_node], 1)]

    for vote in parts_dict["votes"]:
        username = vote[0]
        vote_int = vote[1]
        sources.append(([normalize_uri('/s/contributor/omcs/'+username),
                     normalize_uri(u'/s/activity/omcs/vote')], vote_int))
    return sources

def by_bedume_and_bad(source_list,start,end):
    if 'bedume' in ' '.join(source_list):
        for flagged in BEDUME_FLAGGED_CONCEPTS + BEDUME_FLAGGED_PLACES:
            check = '/'+flagged.replace(' ', '_')
            if start.endswith(check) or end.endswith(check):
                return True
    return False

class CN4Builder(object):
    def __init__(self):
        self.seen_sources = set()

    def handle_raw_assertion(self, flat_assertion):
        parts_dict = json.loads(flat_assertion)
        
        if can_skip(parts_dict):
            return

        # build the assertion
        frame_text = build_frame_text(parts_dict)
        relation = build_relation(parts_dict)
        start = build_start(parts_dict)
        end = build_end(parts_dict)
        dataset = build_data_set(parts_dict)
        sources = build_sources(parts_dict)

        reject = False
        for source_list, weight in sources:
            if 'commons2_reject' in ' '.join(source_list):
                reject = True

        if not reject:
            for source_list, weight in sources:
                if not by_bedume_and_bad(source_list,start,end):
                    contributors = [s for s in source_list if s.startswith('/s/contributor')]
                    assert len(contributors) <= 1, contributors
                    edge = make_edge(relation, start, end, dataset, LICENSE, source_list, '/ctx/all', frame_text, weight=weight)
                    okay = True
                    if contributors:
                        uri = edge['uri']
                        contributor = contributors[0]
                        if (uri, contributor) in self.seen_sources:
                            okay = False
                        else:
                            self.seen_sources.add((uri, contributor))
                    if okay:
                        yield json.dumps(edge, ensure_ascii=False)


if __name__ == '__main__':
    from conceptnet5.readers import transform_stream
    builder = CN4Builder()
    transform_stream(builder.handle_raw_assertion)
