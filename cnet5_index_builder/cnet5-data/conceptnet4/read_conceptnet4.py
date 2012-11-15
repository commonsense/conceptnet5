
import os
import codecs
import sys
import simplenlp

from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri, make_concept_uri
from conceptnet5.quick_reader import QuickReader

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

def can_skip(raw_assertion):
    lang = raw_assertion.language_id
    if lang.startswith('zh'):
        return True
    if raw_assertion.frame.goodness < 1:
        return True

    activity = raw_assertion.sentence.activity.name
    if 'rubycommons' in activity: 
        return True
    return False

def build_frame_text(raw_assertion):
    frame_text = raw_assertion.frame.text
    polarity = raw_assertion.frame.frequency.value
    if polarity > 0:
        frame_text = frame_text.replace('{%}', '')
    else:
        frame_text = frame_text.replace('{%}', 'not')
    frame_text = frame_text.replace('{1}', '[[%s]]' % raw_assertion.text1).replace('{2}', '[[%s]]' % raw_assertion.text2)
    return frame_text

def build_relation(raw_assertion):
    relname = raw_assertion.frame.relation.name
    polarity = raw_assertion.frame.frequency.value
    if relname == 'ConceptuallyRelatedTo':
        relname = 'RelatedTo'

    if polarity > 0:
        relation = normalize_uri('/r/'+relname)
    else:
        relation = normalize_uri('/r/Not'+relname)

    return relation

def build_start(raw_assertion):
    lang = raw_assertion.language_id
    startText = raw_assertion.text1
    start = make_concept_uri(startText, lang)
    return start

def build_end(raw_assertion):
    lang = raw_assertion.language_id
    endText = raw_assertion.text2
    end = make_concept_uri(endText, lang)
    return end

def build_data_set(raw_assertion):
    lang = raw_assertion.language_id
    dataset = normalize_uri('/d/conceptnet/4/'+lang)
    return dataset

def build_sources(raw_assertion):
    activity = raw_assertion.sentence.activity.name

    creator_node = normalize_uri(u'/s/contributor/omcs/'+raw_assertion.creator.username)
    activity_node = normalize_uri(u'/s/activity/omcs/'+activity)
    sources = [([creator_node, activity_node], 1)]

    for vote in raw_assertion.votes.all():
        sources.append(([normalize_uri('/s/contributor/omcs/'+vote.user.username),
                     normalize_uri(u'/s/activity/omcs/vote')], vote.vote))
    return sources

def by_bedume_and_bad(source_list,start,end,raw_assertion):
    if 'bedume' in ' '.join(source_list):
        for flagged in BEDUME_FLAGGED_CONCEPTS + BEDUME_FLAGGED_PLACES:
            check = '/'+flagged.replace(' ', '_')
            if start.endswith(check) or end.endswith(check):
                #print "flagged:", str(raw_assertion)
                return True
    return False

def handle_raw_assertion(raw_assertion):
    try:
        if can_skip(raw_assertion):
            return []

        # build the assertion
        frame_text = build_frame_text(raw_assertion)
        relation = build_relation(raw_assertion)
        start = build_start(raw_assertion)
        end = build_end(raw_assertion)
        dataset = build_data_set(raw_assertion)
        sources = build_sources(raw_assertion)

        edges = []
        for source_list, weight in sources:
            if 'commons2_reject' in ' '.join(source_list):
                weight = -1
            
            if by_bedume_and_bad(source_list,start,end,raw_assertion):
                return []
            else:
                edge = make_edge(relation, start, end, dataset, LICENSE, source_list, '/ctx/all', frame_text, weight=weight)
                edges.append(edge)

        return edges
    except Exception:
        import traceback
        #traceback.print_exc()
        return []


def add_lines_to_queue(q):
    raw_assertions = RawAssertion.objects.filter()
    for raw_assertion in raw_assertions:
        q.put(raw_assertion)

def run_single_process():
    writer = MultiWriter('conceptnet4')
    raw_assertions = RawAssertion.objects.filter()
    for raw_assertion in raw_assertions:
        edges = handle_raw_assertion(raw_assertion)
        for edge in edges:
            writer.write(edge)


if __name__ == '__main__':
    if "--quick_write" in sys.argv:
        quickReader = QuickReader("conceptnet4", handle_raw_assertion,add_lines_to_queue)
        quickReader.start()

    else:
        run_single_process()




