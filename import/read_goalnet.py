import re
from conceptnet5.graph import JSONWriterGraph
from conceptnet5.english_nlp import normalize
from pymongo import Connection
from types import *

GRAPH = JSONWriterGraph('json_data/goalnet')

goalnet = GRAPH.get_or_create_node(u'/source/rule/goalnet')
GRAPH.justify(0, goalnet)
omics = GRAPH.get_or_create_node(u'/source/activity/omics')
GRAPH.justify(0, omics)

def output_steps(goal, steps, source):
    # add raw assertions
    args = []
    for step in steps:
        args.append(GRAPH.get_or_create_concept('en', step))
    raw_sequence = GRAPH.get_or_create_assertion(
        '/relation/Sequence', args,
        {'dataset': 'goalnet/en', 'license': 'CC-By-SA'}
    )
    args = [GRAPH.get_or_create_concept('en', goal)]
    args.append(raw_sequence)
    raw_assertion = GRAPH.get_or_create_assertion(
        '/relation/HasSteps', args,
        {'dataset': 'goalnet/en', 'license': 'CC-By-SA'}
    )
    # add assertions
    args = []
    goal = normalize(goal).strip().lower()
    steps = map(lambda x: normalize(x).strip().lower(), steps)
    for step in steps:
        args.append(GRAPH.get_or_create_concept('en', step))
    sequence = GRAPH.get_or_create_assertion(
        '/relation/Sequence', args,
        {'dataset': 'goalnet/en', 'license': 'CC-By-SA'}
    )
    args = [GRAPH.get_or_create_concept('en', goal)]
    args.append(sequence)
    assertion = GRAPH.get_or_create_assertion(
        '/relation/HasSteps', args,
        {'dataset': 'goalnet/en', 'license': 'CC-By-SA'}
    )
    GRAPH.derive_normalized(raw_sequence, sequence)
    GRAPH.derive_normalized(raw_assertion, assertion)
    # add justification
    if source == 'wikihow':
        pass
        #conjunction = GRAPH.get_or_create_conjunction([wikihow, goalnet, raw_sequence])
        #GRAPH.justify(conjunction, sequence, 0.8)
        #conjunction = GRAPH.get_or_create_conjunction([wikihow, goalnet, raw_assertion])
        #GRAPH.justify(conjunction, assertion, 0.8)
    elif source == 'omics':
        conjunction = GRAPH.get_or_create_conjunction([omics, goalnet, raw_sequence])
        GRAPH.justify(conjunction, sequence)
        conjunction = GRAPH.get_or_create_conjunction([omics, goalnet, raw_assertion])
        GRAPH.justify(conjunction, assertion)
    return assertion

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
            if depth == 0:	# we only consider the steps in top level
                actions.extend(get_steps(step, depth+1))
    print actions
    return actions

def read_goalnet(host='abbith.media.mit.edu', port=27017):
    connection = Connection(host, port)
    db = connection['goaldb']
    plan_collection = db['source_plans']
    for goal in plan_collection.find():
        if not goal.has_key('goal'):
            continue
        #if goal.has_key('wikihow') and len(goal['wikihow']['steps']) > 0:
        #    steps = get_steps(goal['wikihow']['steps'])
        #    output_steps(goal['goal'], steps, 'wikihow')
        if goal.has_key('omics'):
            steps = get_steps(goal['omics']['plans'])
            output_steps(goal['goal'], steps, 'omics')

if __name__ == '__main__':
    read_goalnet()
