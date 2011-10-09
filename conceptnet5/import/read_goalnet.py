import re
from conceptnet5.graph import JSONWriterGraph
from conceptnet5.english_nlp import normalize
from pymongo import Connection
from types import *

GRAPH = JSONWriterGraph('json_data/goalnet')

goalnet = GRAPH.get_or_create_node(u'/source/rule/goalnet')
GRAPH.justify(0, goalnet)
goalnet_plans = GRAPH.get_or_create_node(u'/source/rule/extract_goalnet_plans')
wikihow = GRAPH.get_or_create_node(u'/source/web/www.wikihow.com')
omics = GRAPH.get_or_create_node(u'/source/activity/omics')
GRAPH.justify(0, goalnet_plans)
GRAPH.justify(0, wikihow)
GRAPH.justify(0, omics)

def output_sentence(goal, step, source):
    frame = u"{2} is a step to accomplish the goal: {1}"
    raw = GRAPH.get_or_create_assertion(
        GRAPH.get_or_create_frame('en', frame),
        [GRAPH.get_or_create_concept('en', goal),
         GRAPH.get_or_create_concept('en', step)],
        {'dataset': 'goalnet/en', 'license': 'CC-By-SA'}
    )
    conjunction = None
    if source == 'wikihow':
        conjunction = GRAPH.get_or_create_conjunction([wikihow, goalnet])
        GRAPH.justify(conjunction, raw, 0.8)
    elif source == 'omics':
        conjunction = GRAPH.get_or_create_conjunction([omics, goalnet])
        GRAPH.justify(conjunction, raw)

    goal = normalize(goal).strip()
    step = normalize(step).strip()
    assertion = GRAPH.get_or_create_assertion(
        '/relation/HasStep',
        [GRAPH.get_or_create_concept('en', goal),
         GRAPH.get_or_create_concept('en', step)],
        {'dataset': 'goalnet/en', 'license': 'CC-By-SA'}
    )
    conjunction = GRAPH.get_or_create_conjunction(
        [raw, goalnet_plans]
    )
    GRAPH.justify(conjunction, assertion)
    GRAPH.derive_normalized(raw, assertion)
    return assertion

def output_nested_steps(goal, steps, source):
    if type(steps) is UnicodeType:
        output_sentence(goal, steps, source)
    else:
        # skip some parsing errors of goalnet
        if (type(steps[0]) is ListType) or (len(steps) < 2):
            return
        output_sentence(goal, steps[0], source)
        output_nested_steps(steps[0], steps[1], source)

def remove_wikihow_tag(data):
    p = re.compile(r'LINK\[\[\[.*?\]\]\]')
    data = p.sub('', data)
    p = re.compile(r'IMAGE\[\[\[.*?\]\]\]')
    return p.sub('', data).replace("[[[", "").replace("]]]", "").lstrip()

def get_steps(steps, depth=0):
    actions = []
    for step in steps:
        if type(step) is UnicodeType:
            actions.append(remove_wikihow_tag(step).split('.')[0])
        else:
            if depth == 0:
                actions.extend(get_steps(step, depth+1))
            else:
                actions.append(get_steps(step, depth+1))
    return actions

def read_goalnet(host='abbith.media.mit.edu', port=27017):
    connection = Connection(host, port)
    db = connection['goaldb']
    plan_collection = db['source_plans']
    for goal in plan_collection.find():
        if not goal.has_key('goal'):
            continue
        if goal.has_key('wikihow') and len(goal['wikihow']['steps']) > 0:
            steps = get_steps(goal['wikihow']['steps'])
            output_nested_steps(goal['goal'], steps, 'wikihow')
        if goal.has_key('omics'):
            steps = get_steps(goal['omics']['plans'])
            output_nested_steps(goal['goal'], steps, 'omics')

if __name__ == '__main__':
    read_goalnet()
