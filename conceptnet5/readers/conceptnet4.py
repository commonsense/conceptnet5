from __future__ import unicode_literals
"""
This script reads the ConceptNet 4 data out of the flat files in raw_data,
and builds ConceptNet 5 edges from the data.
"""

from conceptnet5.formats.json_stream import read_json_stream
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import (
    standardized_concept_uri, standardize_text, valid_concept_name
)
from conceptnet5.edges import make_edge
from conceptnet5.uri import join_uri, Licenses

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
  'alaska', 'kansa', 'utah', 'austria', 'delaware', 'pennsylvania', 'italy',
  'cuba', 'norway', 'idaho', 'france', 'utha', 'mexico', 'connecticut',
  'massachusetts', 'montana', 'wyoming', 'every state', 'new york', 'maine',
  'suface of moon', 'germany', 'nebraska', 'finland', 'louisiana', 'belgium',
  'morrocco', 'ireland', 'ceylon', 'california', 'oregon', 'florida',
  'uraguay', 'egypt', 'maryland', 'washington', 'morocco', 'south dakota',
  'tuscon', 'panama', 'alberta', 'arizona', 'texas', 'new jersey', 'colorado',
  'jamaica', 'vermont', 'nevada', 'delawere', 'hawaii', 'minnesota', 'tuscony',
  'costa rica', 'south dakato', 'south dakota', 'china', 'argentina',
  'venazuela', 'honduras', 'opera', 'wisconsin', 'great britain',
]
AROUND_PREPOSITIONS = [
  'in', 'on', 'at', 'under', 'near'
]

# Some specific relations were once added to ConceptNet that have no purpose
# for us anymore, especially ones connected with a project that was trying to
# understand how people describe pain.
#
# 'InheritsFrom' was an inference-related hack on ConceptNet 3 that was never
# supposed to make it into the actual database.

RELATIONS_TO_DROP = {
    '/r/HasPainIntensity', '/r/HasPainCharacter', '/r/InheritsFrom'
}

def can_skip(parts_dict):
    """
    Skip the kinds of data that we don't want to import from ConceptNet 4's
    database dump.

    The activity called 'testing' was actually collecting preliminary data for
    a dataset about subjective medical experiences. This data looks really out
    of place now.
    """
    lang = parts_dict['lang']
    if lang.startswith('zh'):
        # Chinese assertions from GlobalMind are not reliable enough. We'll get
        # Chinese from the `ptt_petgame` module instead.
        return True
    if lang == 'ja' and parts_dict["activity"] != 'nadya.jp':
        # Use Japanese data collected from nadya.jp, but not earlier attempts.
        return True
    if parts_dict["goodness"] < 1:
        return True
    if 'spatial concept' in parts_dict["startText"]:
        return True
    if not parts_dict["startText"] or not parts_dict["endText"]:
        return True
    if 'rubycommons' in parts_dict["activity"]:
        return True
    if 'Verbosity' in parts_dict["activity"]:
        return True
    if 'testing' in parts_dict["activity"]:
        return True
    if not (
        valid_concept_name(parts_dict["startText"]) and
        valid_concept_name(parts_dict["endText"])
    ):
        return True
    return False


def build_frame_text(parts_dict):
    """
    Make a ConceptNet 5 surfaceText out of the ConceptNet 4 assertion's
    frame and surface texts.
    """
    frame_text = parts_dict["frame_text"]
    # Mark frames where {2} precedes {1} with an asterisk.
    if frame_text.find('{1}') > frame_text.find('{2}'):
        frame_text = '*' + frame_text
    polarity = parts_dict["polarity"]

    # If this is a negative frame, then it should either have the negative
    # phrasing baked in, or (in English) the symbol {%} where we can insert
    # the word "not".
    if polarity > 0:
        frame_text = frame_text.replace('{%}', '')
    else:
        frame_text = frame_text.replace('{%}', 'not ')
    frame_text = frame_text.replace('{1}', '[[%s]]' % parts_dict["startText"]).replace('{2}', '[[%s]]' % parts_dict["endText"])
    return frame_text


def build_relation(parts_dict):
    """
    Update relation names to ConceptNet 5's names. Mostly we preserve the same
    names, but any instance of "ConceptuallyRelatedTo" becomes "RelatedTo".
    Statements with negative polarity get new negative relations.
    """
    relname = parts_dict["relname"]
    polarity = polarity = parts_dict["polarity"]
    if relname == 'ConceptuallyRelatedTo':
        relname = 'RelatedTo'

    if polarity > 0:
        relation = join_uri('/r', relname)
    else:
        relation = join_uri('/r', 'Not' + relname)

    return relation


def build_start(parts_dict):
    lang = parts_dict['lang']
    startText = parts_dict["startText"]
    start = standardized_concept_uri(lang, startText)
    return start


def build_end(parts_dict):
    lang = parts_dict['lang']
    endText = parts_dict["endText"]
    end = standardized_concept_uri(lang, endText)
    return end


def build_data_set(parts_dict):
    lang = parts_dict['lang']
    dataset = join_uri('/d/conceptnet/4', lang)
    return dataset


def build_sources(parts_dict, preposition_fix=False):
    """
    Create the 'source' information for an assertion.

    The output is a list of (conjunction, weight) tuples, where 'conjunction'
    is a list of sources that combined to produce this assertion. Later,
    inside the 'make_edge' function, these will be combined into an '/and'
    node.
    """
    activity = parts_dict["activity"]

    creator_node = join_uri(
        '/s/contributor/omcs',
        standardize_text(parts_dict["creator"])
    )
    activity_node = join_uri('/s/activity/omcs', standardize_text(activity))
    if preposition_fix:
        conjunction = [creator_node, activity_node, '/s/rule/preposition_fix']
    else:
        conjunction = [creator_node, activity_node]
    weighted_sources = [(conjunction, 1)]

    for vote in parts_dict["votes"]:
        username = vote[0]
        if username == parts_dict["creator"]:
            continue

        vote_int = vote[1]
        conjunction = [
            join_uri('/s/contributor/omcs', standardize_text(username)),
            '/s/activity/omcs/vote'
        ]
        weighted_sources.append((conjunction, vote_int))
    return weighted_sources


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

    def handle_assertion(self, parts_dict):
        """
        Process one assertion from ConceptNet 4, which appears in the input
        file as a dictionary.

        Use the 'raw' text -- the text that's not yet reduced to a normalized
        form -- so we can run ConceptNet 5's normalization on it instead.

        Each assertion becomes a number of ConceptNet 5 edges, which will
        probably be grouped together into an assertion again.
        """
        if can_skip(parts_dict):
            return

        # fix the result of some process that broke prepositions ages ago
        preposition_fix = False
        if '} around {' in parts_dict['frame_text']:
            for prep in AROUND_PREPOSITIONS:
                if parts_dict['endText'].startswith(prep + ' '):
                    parts_dict['endText'] = \
                        parts_dict['endText'][len(prep) + 1:]
                    replacement = '} %s {' % prep
                    parts_dict['frame_text'] = \
                        parts_dict['frame_text'].replace(
                            '} around {',
                            replacement
                        )
                    preposition_fix = True
                    break

        if can_skip(parts_dict):
            return

        # build the assertion
        frame_text = build_frame_text(parts_dict)
        relation = build_relation(parts_dict)
        start = build_start(parts_dict)
        end = build_end(parts_dict)
        dataset = build_data_set(parts_dict)
        weighted_sources = build_sources(parts_dict, preposition_fix)

        if relation in RELATIONS_TO_DROP:
            return

        if relation == '/r/DesireOf':
            # Fix an inconsistently-named relation from GlobalMind
            relation = '/r/Desires'

        for source_list, weight in weighted_sources:
            if 'commons2_reject' in ' '.join(source_list):
                return

        for source_list, weight in weighted_sources:
            if not by_bedume_and_bad(source_list, start, end):
                yield make_edge(
                    rel=relation, start=start, end=end,
                    dataset=dataset, license=Licenses.cc_attribution,
                    sources=source_list, surfaceText=frame_text,
                    weight=weight
                )

    def transform_file(self, input_filename, output_file):
        out = MsgpackStreamWriter(output_file)
        for obj in read_json_stream(input_filename):
            for new_obj in self.handle_assertion(obj):
                out.write(new_obj)


def handle_file(input_filename, output_file):
    builder = CN4Builder()
    builder.transform_file(input_filename, output_file)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='JSON-stream file of input')
    parser.add_argument('output', help='msgpack file to output to')
    args = parser.parse_args()
    handle_file(args.input, args.output)

if __name__ == '__main__':
    main()
