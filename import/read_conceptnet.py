from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion
from conceptnet5.graph import JSONWriterGraph
from conceptnet5.english_nlp import normalize as en_normalize
import simplenlp

GRAPH = JSONWriterGraph('json_data/conceptnet')

OMCS = GRAPH.get_or_create_node('/source/site/omcs')
GRAPH.justify('/', OMCS)

JA = simplenlp.get('ja')
# monkey-patch
def answer_false(*args):
    return False
JA.is_stopword_record = answer_false

def put_raw_assertion_in_graph(raw):
    try:
        lang = raw.language_id
        if raw.frame.goodness < 1: return
        if lang.startswith('zh'): return
        polarity = raw.frame.frequency.value
        activity = raw.sentence.activity.name
        if 'rubycommons' in activity: return

        # build the assertion
        raw_arg1 = GRAPH.get_or_create_concept(lang, raw.text1)
        raw_arg2 = GRAPH.get_or_create_concept(lang, raw.text2)
        frame_text = raw.frame.text
        if polarity > 0:
            frame_text = frame_text.replace('{%}', '')
        else:
            frame_text = frame_text.replace('{%}', 'not')
        frame = GRAPH.get_or_create_frame(lang, frame_text)
        raw_assertion = GRAPH.get_or_create_assertion(
            frame,
            [raw_arg1, raw_arg2],
            {'dataset': 'conceptnet/4/'+lang, 'license': 'CC-By', 'normalized': False}
        )
        
        # create justification structure
        creator = raw.sentence.creator.username
        if creator == 'verbosity': return
        creator_node = GRAPH.get_or_create_node(
          u'/source/contributor/omcs/'+creator
        )
        activity_node = GRAPH.get_or_create_node(u'/source/activity/omcs/'+activity)
        GRAPH.justify(OMCS, activity_node)
        GRAPH.justify(OMCS, creator_node)
        conjunction = GRAPH.get_or_create_conjunction(
            [creator_node, activity_node]
        )
        GRAPH.justify(conjunction, raw_assertion)

        # make the normalized version
        if lang == 'en':
            arg1 = GRAPH.get_or_create_concept('en', en_normalize(raw.text1))
            arg2 = GRAPH.get_or_create_concept('en', en_normalize(raw.text2))
        elif lang == 'ja':
            arg1 = GRAPH.get_or_create_concept('ja', JA.normalize(raw.text1))
            arg2 = GRAPH.get_or_create_concept('ja', JA.normalize(raw.text2))
        else:
            nlp = simplenlp.get(lang)
            arg1 = GRAPH.get_or_create_concept(lang, nlp.normalize(raw.text1))
            arg2 = GRAPH.get_or_create_concept(lang, nlp.normalize(raw.text2))

        if polarity > 0:
            relation = GRAPH.get_or_create_relation(raw.frame.relation.name)
        else:
            relation = GRAPH.get_or_create_relation('Not'+raw.frame.relation.name)
        assertion = GRAPH.get_or_create_assertion(
            relation, [arg1, arg2],
            {'dataset': 'conceptnet/4/'+lang, 'license': 'CC-By', 'normalized': True}
        )
        for vote in raw.votes.all():
            voter = GRAPH.get_or_create_node(
              u'/source/contributor/omcs/'+vote.user.username
            )
            GRAPH.justify(OMCS, voter)
            GRAPH.justify(voter, raw_assertion, weight=vote.vote)

        GRAPH.derive_normalized(raw_assertion, assertion)
        print assertion
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    queryset_foreach(RawAssertion, put_raw_assertion_in_graph)
