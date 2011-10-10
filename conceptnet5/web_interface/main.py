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
  frames = []
  normalizations = []
  for (relation, unused_relation_start) in incoming_edges:
    # Get the type of relation this edge represents.
    if relation[u'type'] == u'arg':
      assertion_uri = relation[u'start']
      assertion = conceptnet.get_node(assertion_uri)
      # TODO(jven): we assume all this stuff exists
      assertion_relation_uri = assertion[u'relation']
      assertion_relation = conceptnet.get_node(assertion_relation_uri)
      assertion_relation_type = assertion_relation[u'type']
      assertion_args_uri = assertion[u'args']
      assertion_args = [conceptnet.get_node(uri) for uri in assertion_args_uri]
      assertion_arg_left = assertion_args[0]
      assertion_args_right = assertion_args[1:]
      if assertion_relation_type == u'frame':
        rendered_frame = assertion_relation[u'name']
        for idx in xrange(len(assertion_args)):
          arg = assertion_args[idx]
          rendered_frame = rendered_frame.replace('{%d}' % (idx + 1),
              arg[u'name'])
        frames.append(rendered_frame)
      else:
        assertions.append([assertion_relation, assertion_arg_left,
            assertion_args_right])
    elif relation[u'type'] == u'normalized':
      normalizations.append((relation[u'start'], relation[u'end']))
  return render_template('data.html', assertions=assertions, frames=frames,
      normalizations=normalizations)

@app.errorhandler(404)
def handler404(error):
  return render_template('404.html')

if __name__ == '__main__':
  app.run(debug=True)
