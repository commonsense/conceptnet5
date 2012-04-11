from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri
import simplenlp

#JA = simplenlp.get('ja')
# monkey-patch
#def answer_false(*args):
#    return False
#JA.is_stopword_record = answer_false

LICENSE = '/l/CC/By'

def handle_raw_assertion(raw, writer):
    try:
        lang = raw.language_id
        if raw.frame.goodness < 1: return
        if lang.startswith('zh'): return
        polarity = raw.frame.frequency.value
        activity = raw.sentence.activity.name
        if 'rubycommons' in activity: return

        # build the assertion
        frame_text = raw.frame.text
        if polarity > 0:
            frame_text = frame_text.replace('{%}', '')
        else:
            frame_text = frame_text.replace('{%}', 'not')
        frame_text = frame_text.replace('{1}', '[[%s]]' % raw.text1).replace('{2}', '[[%s]]' % raw.text2)

        creator_node = normalize_uri(u'/s/contributor/omcs/'+raw.creator.username)
        activity_node = normalize_uri(u'/s/activity/omcs/'+activity)
        
        startText = raw.text1
        endText = raw.text2
        normalize_uri('/text/'+lang+'/'+raw.text1)
        end = normalize_uri('/text/'+lang+'/'+raw.text2)

        if polarity > 0:
            relation = normalize_uri('/r/'+raw.frame.relation.name)
        else:
            relation = normalize_uri('/r/Not'+raw.frame.relation.name)

        dataset = normalize_uri('/d/conceptnet/4/'+lang)

        sources = [([creator_node, activity_node], 1)]
        for vote in raw.votes.all():
            sources.append(([normalize_uri('/s/contributor/omcs/'+vote.user.username),
                             normalize_uri(u'/s/activity/omcs/vote')], vote.vote))

        for source_list, weight in sources:
            edge = make_edge(relation, startText, lang, endText, lang, dataset, LICENSE, source_list, frame_text, weight=weight)
            writer.write(edge)
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    writer = MultiWriter('conceptnet4')
    queryset_foreach(RawAssertion.objects.filter(), lambda item: handle_raw_assertion(item, writer))
    writer.close()
