# This file must be run while config.py points to the "nadya" database instead
# of "ConceptNet".
#
# Unfortunately, all of this was done before Django had multi-database support.

from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri, make_concept_uri
from metanl import japanese
from conceptnet5.quick_reader import QuickReader
import sys

JA = japanese.NoStopwordMeCabWrapper()

LICENSE = '/l/CC/By'

def can_skip(raw_assertion):
    lang = raw_assertion.language_id
    if lang != 'ja':
        return True
    if raw_assertion.frame.goodness < 1:
        return True

    activity = raw_assertion.sentence.activity.name
    if 'rubycommons' in activity: 
        return True
    return False

def build_frame_text(raw_assertion):
    frame_text = raw_assertion.frame.text
    frame_text = frame_text.replace('{1}', '[[%s]]' % raw_assertion.text1).replace('{2}', '[[%s]]' % raw_assertion.text2)
    return frame_text

def build_relation(raw_assertion):
    polarity = raw_assertion.frame.frequency.value
    relname = raw_assertion.frame.relation.name
    if relname == 'ConceptuallyRelatedTo':
        relname = 'RelatedTo'

    if polarity > 0:
        relation = normalize_uri('/r/'+relname)
    else:
        relation = normalize_uri('/r/Not'+relname)
    return relation

def build_start(raw_assertion):
    lang = raw_assertion.language_id
    startText = ' '.join(JA.normalize_list(raw_assertion.text1))
    start = make_concept_uri(startText, lang)
    return start

def build_end(raw_assertion):
    lang = raw_assertion.language_id
    endText = ' '.join(JA.normalize_list(raw_assertion.text2))
    end = make_concept_uri(endText, lang)
    return end

def build_sources(raw_assertion):
    score = raw_assertion.score
    activity_node = normalize_uri(u'/s/site/nadya.jp')
    sources = [([activity_node], score/5.)]
    return sources

def build_data_set():
    return normalize_uri('/d/nadya.jp')

def handle_raw_assertion(raw_assertion):
    try:
        if can_skip(raw_assertion):
            return []

        frame_text = build_frame_text(raw_assertion)
        relation = build_relation(raw_assertion)
        start = build_start(raw_assertion)
        end = build_end(raw_assertion)
        dataset = build_data_set()
        sources = build_sources(raw_assertion)

        edges = []
        for source_list, weight in sources:
            if 'commons2_reject' in ' '.join(source_list):
                weight = -1

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
    writer = MultiWriter('conceptnet4_nadya')
    raw_assertions = RawAssertion.objects.filter()
    for raw_assertion in raw_assertions:
        edges = handle_raw_assertion(raw_assertion)
        for edge in edges:
            writer.write(edge)


if __name__ == '__main__':
    if "--quick_write" in sys.argv:
        quickReader = QuickReader("conceptnet_nadya", handle_raw_assertion,add_lines_to_queue)
        quickReader.start()

    else:
        run_single_process()
