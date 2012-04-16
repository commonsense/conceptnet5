from flask import Flask, redirect, render_template, request, send_from_directory
import random
import os
import time
import json
import codecs

app = Flask(__name__)
@app.route('/')
def randomize():
    prefix = "%04x" % random.randrange(0, 16**4)
    
    return redirect('/evaluate/%s' % prefix)

def readable(uri):
    parts = uri.split('/')
    disambig = None
    if len(parts) > 5:
        disambig = uri.split('/')[5].replace('_', ' ')
    if uri.startswith('/r/'):
        concept = uri.split('/')[2].replace('_', ' ')
        if concept == 'InstanceOf':
            concept = 'is a'
    else:
        concept = uri.split('/')[3].replace('_', ' ')
    if disambig:
        return u'%s (<i>%s</i>)' % (concept, disambig)
    else:
        return concept

@app.route('/respond', methods=['POST'])
def respond():
    data = {}
    for key in request.form:
        type, id = key.split('-')
        if not data.has_key(id):
            data[id] = {}
        data[id][type] = request.form[key]

    results = {
        'headers': dict(request.headers),
        'values': data
    }
    out = open('responses/%d' % time.time(), 'w')
    json.dump(results, out, indent=2)
    return render_template('thanks.html')


@app.route('/evaluate/<prefix>')
def evaluate(prefix):
    assert len(prefix) == 4 and all([letter in '0123456789abcdef' for letter in prefix])
    # crappy way to get data! go!
    prefix3 = prefix[:3]
    if not os.access('data/%s.csv' % prefix3, os.F_OK):
        os.system("grep /e/%s ../import/data/flat/all.csv > data/%s.csv" % (prefix3, prefix3))
    skipped = False
    statements = []
    random.seed(int(prefix, 16))
    for line in codecs.open('data/%s.csv' % prefix3, encoding='utf-8'):
        if not skipped:
            skipped = True
        else:
            uri, rel, start, end, context, weight, sources, id, dataset, text = line.strip('\n').split('\t')
            if 'dbpedia' in dataset and random.random() > .25:
                continue
            elif 'wiktionary' in dataset and random.random() > .5:
                continue
            if ':' in start or ':' in end or 'Wiktionary' in line or 'Category' in line:
                continue
            if not '/c/en' in line:
                continue
            if text is None or text == 'None':
                subj = readable(start)
                obj = readable(end)
                rel = readable(rel)
                text = "[[%s]] %s [[%s]]" % (subj, rel, obj)

            text = text.replace('[[', '<b>').replace(']]', '</b>')
            if weight < 0:
                uri += '/'
            statements.append(dict(
                id=id[3:],
                uri=uri,
                dataset=dataset,
                text=text,
                weight=weight
            ))

    neg_statements = [s for s in statements if s['weight'] < 0]
    pos_statements = [s for s in statements if s['weight'] > 0]
    num_to_sample = min(len(pos_statements), max(1, 25 - len(neg_statements)))
    shown_statements = neg_statements + random.sample(pos_statements, num_to_sample)
    random.shuffle(shown_statements)

    return render_template('evaluate.html', statements=shown_statements)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)
