# This file must be run while config.py points to the "nadya" database instead
# of "ConceptNet".
#
# Unfortunately, all of this was done before Django had multi-database support.

from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri, make_concept_uri
from metanl import japanese

JA = japanese.NoStopwordMeCabWrapper()

LICENSE = '/l/CC/By'

def handle_raw_assertion(raw, writer):
    try:
        lang = raw.language_id
        if lang == 'ja':
            if raw.frame.goodness < 1: return
            polarity = raw.frame.frequency.value
            activity = raw.sentence.activity.name
            if 'rubycommons' in activity: return

            # build the assertion
            frame_text = raw.frame.text
            frame_text = frame_text.replace('{1}', '[[%s]]' % raw.text1).replace('{2}', '[[%s]]' % raw.text2)

            activity_node = normalize_uri(u'/s/site/nadya.jp')
            
            startText = ' '.join(JA.normalize_list(raw.text1))
            endText = ' '.join(JA.normalize_list(raw.text2))
            # if startText != raw.text1:
            #     print raw.text1.encode('utf-8'), '=>',  startText.encode('utf-8')
            normalize_uri('/text/'+lang+'/'+startText)
            end = normalize_uri('/text/'+lang+'/'+endText)

            relname = raw.frame.relation.name
            if relname == 'ConceptuallyRelatedTo':
                relname = 'RelatedTo'

            if polarity > 0:
                relation = normalize_uri('/r/'+relname)
            else:
                relation = normalize_uri('/r/Not'+relname)

            dataset = normalize_uri('/d/nadya.jp')
            score = raw.score

            sources = [([activity_node], score/5.)]

            for source_list, weight in sources:
                if 'commons2_reject' in ' '.join(source_list):
                    weight = -1
                start = make_concept_uri(startText, lang)
                end = make_concept_uri(endText, lang)
                edge = make_edge(relation, start, end, dataset, LICENSE, source_list, '/ctx/all', frame_text, weight=weight)
                writer.write(edge)
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    writer = MultiWriter('nadya.jp')
    raw_assertions = RawAssertion.objects.filter()
    for item in raw_assertions:
        handle_raw_assertion(item,writer)
    #queryset_foreach(RawAssertion.objects.filter(), lambda item: handle_raw_assertion(item, writer))
    writer.close()
