"""
Web interface for ConceptNet5.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

from flask import Flask
from conceptnet5.graph import get_graph

app = Flask(__name__)
conceptnet = get_graph()

@app.route('/')
def main():
  return 'Hello world!'

@app.route('/web/<path:uri>')
def get_data(uri):
  uri = '/%s' % uri
  node = conceptnet.get_node(uri)
  return str(node)

if __name__ == '__main__':
  app.run(debug=True)
