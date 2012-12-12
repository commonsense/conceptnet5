
import os
import codecs
import sys
import simplenlp
import re

from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri, make_concept_uri
from conceptnet5.quick_reader import QuickReader


"""
This script reads the conceptnet4 data out of the flat files in raw_data
and builds conceptnet5 edges from the data.  
"""


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


def extract_parts(flat_assertion):
    parts_dict = {}
    
    parts_dict["lang"] = re.findall('(?<=<lang>).*(?=</lang>)', flat_assertion)[0]
    parts_dict["creator"] = re.findall('(?<=<creator>).*(?=</creator>)', flat_assertion)[0]
    parts_dict["frame_id"] = int(re.findall('(?<=<frame_id>).*(?=</frame_id>)', flat_assertion)[0])
    parts_dict["startText"] = re.findall('(?<=<startText>).*(?=</startText>)', flat_assertion)[0]
    parts_dict["endText"] = re.findall('(?<=<endText>).*(?=</endText>)', flat_assertion)[0]
    parts_dict["activity"] = re.findall('(?<=<activity>).*(?=</activity>)', flat_assertion)[0]
    parts_dict["relname"] = re.findall('(?<=<relname>).*(?=</relname>)', flat_assertion)[0]
    parts_dict["polarity"] = float(re.findall('(?<=<polarity>).*(?=</polarity>)', flat_assertion)[0])
    parts_dict["goodness"] = float(re.findall('(?<=<goodness>).*(?=</goodness>)', flat_assertion)[0])
    parts_dict["frame_text"] = re.findall('(?<=<frame_text>).*(?=</frame_text>)', flat_assertion)[0]
    parts_dict["cnet4_id"] = int(re.findall('(?<=<cnet4_id>).*(?=</cnet4_id>)', flat_assertion)[0])
    
    raw_votes = re.findall('(?<=<votes>).*(?=</votes>)', flat_assertion)[0].split("<vote>")[1:]
    votes_list = []
    for raw_vote in raw_votes:
        raw_vote = raw_vote[:-7]
        parts = raw_vote.split(": ")
        vote_username = parts[0]
        vote_int = int(parts[1].split(" ")[0])
       
        votes_list.append((vote_username, vote_int))

    parts_dict["votes"] = votes_list

    return parts_dict

def handle_raw_flat_assertion(flat_assertion):
    try:
        parts_dict = extract_parts(flat_assertion)
        
        if can_skip(parts_dict):
            return []

        # build the assertion
        frame_text = build_frame_text(parts_dict)
        relation = build_relation(parts_dict)
        start = build_start(parts_dict)
        end = build_end(parts_dict)
        dataset = build_data_set(parts_dict)
        sources = build_sources(parts_dict)

        edges = []
        for source_list, weight in sources:
            if 'commons2_reject' in ' '.join(source_list):
                weight = -1
            
            if by_bedume_and_bad(source_list,start,end):
                return []
            else:
                edge = make_edge(relation, start, end, dataset, LICENSE, source_list, '/ctx/all', frame_text, weight=weight)
                edges.append(edge)

        return edges
    except Exception:
        import traceback
        print "failed on flat_assertion: " + str(flat_assertion)
        traceback.print_exc()
        return []


def pull_lines_from_raw_flat_files(q):
    path = "./raw_data/"
    for filename in os.listdir(path):
        for line in codecs.open(path + filename, encoding='utf-8', errors='replace'):
            q.put(line)


if __name__ == '__main__':
    if "--build_from_flat" in sys.argv:
        quickReader = QuickReader("conceptnet4", handle_raw_flat_assertion,pull_lines_from_raw_flat_files)
        quickReader.start()





