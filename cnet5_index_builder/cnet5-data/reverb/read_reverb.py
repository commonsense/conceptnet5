import codecs, string
from metanl.english import normalize
from conceptnet5.nodes import make_concept_uri
from conceptnet5.edges import make_edge, MultiWriter
import json

# Unfortunately, the current file contains a mix of normalized and unnormalized
# output, based on the way things worked in the beta of ConceptNet 5. In fact,
# we have to combine both of them to get all the relevant information.
#
# We should develop a better process for this, but right now we will assume
# that a normalized and unnormalized statement are related if they have the
# same floating-point number as their score and appear adjacent in the file.


def output_edge(obj):
    objsource = obj['sources'][0]
    if obj['arg1'].startswith(objsource):
        obj['arg1'] = objsource
    if obj['arg2'].startswith(objsource):
        obj['arg2'] = objsource
    if obj['arg1'].endswith(objsource):
        obj['arg1'] = objsource
    if obj['arg2'].endswith(objsource):
        obj['arg2'] = objsource
    start = make_concept_uri(obj['arg1'], 'en')
    end = make_concept_uri(obj['arg2'], 'en')
    if obj['rel'][0] in string.uppercase:
        rel = '/r/'+obj['rel']
    else:
        rel = make_concept_uri(obj['rel'], 'en')
    if start.startswith('/c/en/this_') or start.startswith('/c/en/these_') or end.startswith('/c/en/this_') or end.startswith('/c/en/these_'):
        return
    context = make_concept_uri(objsource, 'en')
    source = "/s/web/en.wikipedia.org/wiki/%s" % (objsource.replace(' ', '_'))
    rules = ['/s/rule/reverb', '/s/rule/reverb_filter_apr2012']
    surfaceText = u"[[%s]] %s [[%s]]" % (obj['arg1'], obj.get('surfaceRel', obj['rel']), obj['arg2'])
    weight = float(obj['weight']) ** 3 / 2
    edge = make_edge(rel, start, end,
                     dataset='/d/reverb/wp_frontpage',
                     license='/l/CC/By-SA',
                     sources=[source] + rules,
                     context=context,
                     surfaceText=surfaceText,
                     weight=weight)
    print weight, rel, surfaceText.encode('utf-8')
    writer.write(edge)

def main():
    writer = MultiWriter('reverb-wp-frontpage')
    current_obj = None
    current_score = None
    for line in codecs.open('raw_data/reverb_featured_triples.txt', encoding='utf-8', errors='replace'):
        line = line.strip()
        if line and not line.startswith('['):
            obj = json.loads(line)
            if current_obj is None:
                current_obj = obj
                current_score = obj['weight']
                obj['surfaceRel'] = obj['rel']
            elif obj['weight'] == current_score:
                if normalize(obj['arg1']) == normalize(current_obj['arg1']) and normalize(obj['arg2']) == normalize(current_obj['arg2']):
                    current_obj['rel'] = obj['rel']
                output_edge(current_obj)
                current_obj = None
                current_score = None
            else:
                if current_obj is not None:
                    output_edge(current_obj)
                current_obj = obj
                current_score = obj['weight']
                obj['surfaceRel'] = obj['rel']
    if current_obj is not None:
        output_edge(current_obj)

    writer.close()

if __name__ == '__main__':
    main()