"""
Web interface for ConceptNet5.
"""

__author__ = 'Justin Venezuela (jven@mit.edu)'

from flask import Flask
from flask import render_template
from flask import url_for
from conceptnet5.graph import get_graph

app = Flask(__name__)
conceptnet = get_graph()

@app.route('/')
def main():
  return render_template('home.html')

@app.route('/web/<path:uri>')
def get_data(uri):
  uri = '/%s' % uri
  node = conceptnet.get_node(uri)
  return str(node)

if __name__ == '__main__':
  app.run(debug=True)
