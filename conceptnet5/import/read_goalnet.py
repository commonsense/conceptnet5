import re
from conceptnet5.graph import JSONWriterGraph
from conceptnet5.english_nlp import normalize
from pymongo import Connection
from types import *

GRAPH = JSONWriterGraph('json_data/goalnet')

goalnet = GRAPH.get_or_create_node(u'/source/rule/goalnet')
GRAPH.justify(0, goalnet)
wikihow = GRAPH.get_or_create_node(u'/source/web/www.wikihow.com')
omics = GRAPH.get_or_create_node(u'/source/activity/omics')
GRAPH.justify(0, wikihow)
GRAPH.justify(0, omics)

def output_steps(goal, steps, source):
    goal = normalize(goal).strip()
    steps = map(lambda x: normalize(x).strip(), steps)
    args = [GRAPH.get_or_create_concept('en', goal)]
    for step in steps:
        args.append(GRAPH.get_or_create_concept('en', step))
    assertion = GRAPH.get_or_create_assertion(
        '/relation/HasSteps', args,
        {'dataset': 'goalnet/en', 'license': 'CC-By-SA'}
    )
    if source == 'wikihow':
        conjunction = GRAPH.get_or_create_conjunction([wikihow, goalnet])
        GRAPH.justify(conjunction, assertion, 0.8)
    elif source == 'omics':
        conjunction = GRAPH.get_or_create_conjunction([omics, goalnet])
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
            output_steps(goal['goal'], steps, 'wikihow')
        if goal.has_key('omics'):
            steps = get_steps(goal['omics']['plans'])
            output_steps(goal['goal'], steps, 'omics')

if __name__ == '__main__':
    read_goalnet()
