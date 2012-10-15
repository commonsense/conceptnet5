from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion
from conceptnet5.edges import MultiWriter, make_edge
from conceptnet5.nodes import normalize_uri, make_concept_uri
import simplenlp


#JA = simplenlp.get('ja')
# monkey-patch
#def answer_false(*args):
#    return False
#JA.is_stopword_record = answer_false

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

        relname = raw.frame.relation.name
        if relname == 'ConceptuallyRelatedTo':
            relname = 'RelatedTo'

        if polarity > 0:
            relation = normalize_uri('/r/'+relname)
        else:
            relation = normalize_uri('/r/Not'+relname)

        dataset = normalize_uri('/d/conceptnet/4/'+lang)

        sources = [([creator_node, activity_node], 1)]

        for vote in raw.votes.all():
            sources.append(([normalize_uri('/s/contributor/omcs/'+vote.user.username),
                             normalize_uri(u'/s/activity/omcs/vote')], vote.vote))
        
        for source_list, weight in sources:
            bad = False
            if 'commons2_reject' in ' '.join(source_list):
                weight = -1
            start = make_concept_uri(startText, lang)
            end = make_concept_uri(endText, lang)
            if 'bedume' in ' '.join(source_list):
                for flagged in BEDUME_FLAGGED_CONCEPTS + BEDUME_FLAGGED_PLACES:
                    check = '/'+flagged.replace(' ', '_')
                    if start.endswith(check) or end.endswith(check):
                        bad = True
                        print "flagged:", str(raw)
                        break
            if not bad:
                edge = make_edge(relation, start, end, dataset, LICENSE, source_list, '/ctx/all', frame_text, weight=weight)
                writer.write(edge)
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    writer = MultiWriter('conceptnet4')
    raw_assertions = RawAssertion.objects.filter()
    for item in raw_assertions:
        handle_raw_assertion(item,writer)
    #queryset_foreach(RawAssertion.objects.filter(), lambda item: handle_raw_assertion(item, writer))
    writer.close()
