import json
import codecs
from collections import defaultdict

responses = json.load(open('responses/with_weights.json'))
by_dataset = defaultdict(lambda: defaultdict(float))

for response_group in responses:
    for response in response_group['values'].values():
        if response.has_key('rating'):
            dataset = response['dataset']
            rating = response['rating']
            weight = response['weight']
            if weight < 0:
                dataset = 'negated'
            if 'globalmind' in dataset and 'Translation' in response['uri']:
                dataset = '/d/globalmind/tr'
            if dataset.startswith('/d/conceptnet/4') and dataset != '/d/conceptnet/4/en':
                dataset = '/d/conceptnet/4/other'
            if dataset.startswith('/d/wiktionary') and dataset != '/d/wiktionary/en/en':
                dataset = '/d/wiktionary/other'
            by_dataset[dataset][rating] += 1

out = open('responses/by_dataset.json', 'w')
json.dump(by_dataset, out, default=dict, indent=2)
