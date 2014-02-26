from __future__ import print_function, unicode_literals
from conceptnet5.uri import ROOT_URL
import sys
import urllib
import codecs

SAME_AS = 'http://www.w3.org/2002/07/owl#sameAs'


if sys.version_info.major >= 3:
    unquote = urllib.parse.unquote_to_bytes
    quote = urllib.parse.quote
    urlsplit = urllib.parse.urlsplit
    string_type = str
else:
    import urlparse
    urlsplit = urlparse.urlsplit
    unquote = urllib.unquote
    quote = urllib.quote
    string_type = basestring


def decode_url(url):
    """
    Take in a URL that is percent-encoded for use in a format such as HTML or
    N-triples, and convert it to a Unicode URL.
    """
    return unquote(url).decode('utf-8', 'replace')


def resource_name(url):
    """
    Get a concise name for a Semantic Web resource, given its URL.
    
    This is either the "fragment" identifier, or the path after '/resource/',
    or the item after the final slash.

    There's a special case for '/resource/' because resource names are Wikipedia
    article names, which are allowed to contain additional slashes.
    
    On a Semantic Web URL, this has the effect of getting an object's effective
    "name" while ignoring the namespace and details of where it is stored.
    """
    parsed = urlsplit(decode_url(url))
    if parsed.fragment:
        return parsed.fragment
    else:
        path = parsed.path.strip('/')
        if '/resource/' in path:
            return path.split('/resource/')[-1]
        else:
            return path.split('/')[-1]


def full_conceptnet_url(uri):
    """
    Translate a ConceptNet URI into a fully-specified URL.

    >>> full_conceptnet_url('/c/en/dog')
    'http://conceptnet5.media.mit.edu/data/5.2/c/en/dog'
    """
    assert uri.startswith('/')
    return ROOT_URL + quote(uri)


def same_as_triple(node1, node2):
    """
    Output a Semantic Web triple, as a line in N-triples format,
    saying that node1 and node2 are the same.
    """
    return '<%s> <%s> <%s>' % (node1, SAME_AS, node2)


class NTriplesWriter(object):
    """
    Write to a file in N-Triples format.

    N-Triples is a very simple format for expressing RDF relations. It is
    a sequence of lines of the form

    <node1> <relation> <node2> .

    The angle brackets are literally present in the lines, and the things
    they contain are URLs.

    The suggested extension for this format is '.nt'.
    """
    def __init__(self, filename_or_stream):
        if isinstance(filename_or_stream, string_type):
            self.stream = codecs.open(filename_or_stream, 'w', encoding='ascii')
        else:
            self.stream = filename_or_stream
        self.seen = set()

    def write(self, triple):
        """
        Write a triple of (node1, rel, node2) to a file, if it's not already there.
        """
        if triple not in self.seen:
            self.seen.add(triple)
            line = '<%s> <%s> <%s>' % triple
            print(line, file=self.stream)
    
    def write_same_as(self, node1, node2):
        """
        Write a line expressing that node1 is the same as node2.
        """
        self.write((node1, SAME_AS, node2))

    def close(self):
        if self.stream is not sys.stdout:
            self.stream.close()

