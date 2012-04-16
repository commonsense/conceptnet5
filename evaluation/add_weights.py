import json
import codecs
from collections import defaultdict

responses = json.load(open('responses/all_responses.json'))
edge_ids = set()
edge_values = defaultdict(float)

for response_group in responses:
    for id in response_group['values']:
        edge_ids.add('/e/'+id)

count = 0
for line in codecs.open('../import/data/flat/ALL.csv'):
    uri, rel, start, end, context, weight, sources, id, rest = line.split('\t', 8)
    if weight == 'weight': continue
    weight = float(weight)
    count += 1
    if count % 10000 == 0:
        print count
    if id in edge_ids:
        if weight < 0:
            print id, weight
        edge_values[id] = float(weight)

for response_group in responses:
    for id, response in response_group['values'].items():
        response['weight'] = edge_values['/e/'+id]

out = open('responses/with_weights.json', 'w')
json.dump(responses, out, indent=2)
