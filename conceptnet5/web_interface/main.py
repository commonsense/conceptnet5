"""
Web interface for ConceptNet5.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

import os
from flask import Flask
from flask import redirect
from flask import render_template
from flask import send_from_directory
from flask import url_for
from conceptnet5.graph import get_graph

app = Flask(__name__)
conceptnet = get_graph()

@app.route('/favicon.ico')
def favicon():
  return send_from_directory(
      os.path.join(app.root_path, 'static', 'img'), 'favicon.ico',
      mimetype='image/vnd.microsoft.icon')

@app.route('/')
def home():
  return render_template('home.html')

@app.route('/web/<path:uri>')
def get_data(uri):
  uri = '/%s' % uri
  node = conceptnet.get_node(uri)
  # If node doesn't exist, say so.
  if node is None:
    return render_template('not_found.html', uri=uri)
  # Node exists, show stuff.
  incoming_edges = conceptnet.get_incoming_edges(node)
  assertions = []
  normalizations = []
  for (relation, unused_relation_start) in incoming_edges:
    # Get the type of relation this edge represents.
    if relation[u'type'] == u'arg':
      assertions.append(relation[u'start'])
    elif relation[u'type'] == u'normalized':
      normalizations.append((relation[u'start'], relation[u'end']))
  return render_template('data.html', assertions=assertions,
      normalizations=normalizations)

@app.errorhandler(404)
def handler404(error):
  return render_template('404.html')

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=8000)
