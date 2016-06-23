from ftfy.fixes import decode_escapes
import sys
import urllib
import langcodes
import re

SEE_ALSO = 'http://www.w3.org/2000/01/rdf-schema#seeAlso'


unquote = urllib.parse.unquote_to_bytes
quote = urllib.parse.quote
urlsplit = urllib.parse.urlsplit


def decode_url(url):
    """
    Take in a URL that is percent-encoded for use in a format such as HTML or
    N-triples, and convert it to a Unicode URL.

    If the URL is contained in angle brackets because it comes from an
    N-triples file, strip those.

    >>> decode_url('<http://dbpedia.org/resource/N%C3%BAria_Espert>')
    'http://dbpedia.org/resource/Núria_Espert'
    """
    url_bytes = url.strip('<>').encode('utf-8')
    text = unquote(url_bytes).decode('utf-8', 'replace')
    try:
        return decode_escapes(text)
    except UnicodeDecodeError:
        return text


def safe_quote(uri):
    """
    Represent a URL in a form that no system should find objectionable.

    Encode non-ASCII characters as UTF-8 and then quote them. Consider
    the special URL characters :, #, and / to be "safe" to represent
    as themselves, because we want them to have their URL meaning.

    This can be used on both DBPedia URLs and ConceptNet URIs.

    >>> safe_quote('http://dbpedia.org/resource/Núria_Espert')
    'http://dbpedia.org/resource/N%C3%BAria_Espert'
    >>> safe_quote('/c/en/Núria_Espert')
    '/c/en/N%C3%BAria_Espert'
    """
    return quote(uri.encode('utf-8'), safe=b':/#')


def encode_url(url):
    """
    Reverses the operation of `decode_url` by using percent-encoding and
    surrounding the URL in angle brackets.

    >>> encode_url('http://dbpedia.org/resource/Núria_Espert')
    '<http://dbpedia.org/resource/N%C3%BAria_Espert>'
    """
    return '<%s>' % safe_quote(url)


def resource_name(url):
    """
    Get a concise name for a Semantic Web resource, given its URL.

    This is either the "fragment" identifier, or the path after '/resource/',
    or the item after the final slash.

    There's a special case for '/resource/' because resource names are Wikipedia
    article names, which are allowed to contain additional slashes.

    On a Semantic Web URL, this has the effect of getting an object's effective
    "name" while ignoring the namespace and details of where it is stored.

    >>> resource_name('<http://dbpedia.org/resource/N%C3%BAria_Espert>')
    'Núria_Espert'
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


class NTriplesWriter:
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
        if hasattr(filename_or_stream, 'write'):
            self.stream = filename_or_stream
        else:
            self.stream = open(filename_or_stream, 'w', encoding='ascii')
        self.seen = set()

    def write(self, triple):
        """
        Write a triple of (node1, rel, node2) to a file, if it's not already
        there.
        """
        if triple not in self.seen:
            self.seen.add(triple)
            line_pieces = [encode_url(item) for item in triple] + ['.']
            line = ' '.join(line_pieces)
            print(line, file=self.stream)

    def close(self):
        if self.stream is not sys.stdout:
            self.stream.close()


class NTriplesReader:
    """
    A class for reading multiple files in N-Triples format, keeping track of
    prefixes that they define and expanding them when they appear.

    The URIs in the N-Triples can contain Unicode in UTF-8, which technically
    makes them IRIs, and technically makes the file N-Quads with no graphs,
    as N-Triples doesn't allow Unicode. But for now let's just call that a
    variant of N-Triples that we can handle.
    """
    def __init__(self):
        self.prefixes = {'_': '_'}

    def parse_file(self, filename):
        for line in open(filename, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#'):
                result = self.parse_line(line)
                if result is not None:
                    yield result

    def parse_line(self, line):
        subj, rel, objdot = line.split(' ', 2)
        obj, dot = objdot.rsplit(' ', 1)
        assert dot == '.'
        if subj == '@prefix':
            # Handle prefix definitions, which are lines that look like:
            # @prefix wn30: <http://purl.org/vocabularies/princeton/wn30/> .
            prefix = rel
            prefixname = prefix.rstrip(':')
            self.prefixes[prefixname] = decode_url(obj)
            return None
        else:
            # We assume that `subj` and `rel` are URLs, or can be treated as URLs.
            # `obj` might be a literal text, however, so we need to actually look
            # at what it's tagged with.
            subj_url = self.resolve_node(subj)[1]
            rel_url = self.resolve_node(rel)[1]
            obj_tag, obj_url = self.resolve_node(obj)
            return subj_url, rel_url, obj_url, obj_tag

    def resolve_node(self, node_text):
        """
        Given a Semantic Web node expressed in the N-Triples syntax, expand
        it to either its full, decoded URL or its natural language text
        (whichever is appropriate).

        Returns (lang, text), where `lang` is a language code or the string 'URL'.
        If `lang` is 'URL', the `text` is the expanded, decoded URL.

        >>> reader = NTriplesReader()
        >>> reader.parse_line('@prefix wn30: <http://purl.org/vocabularies/princeton/wn30/> .')
        >>> reader.resolve_node('wn30:synset-Roman_alphabet-noun-1')
        ('URL', 'http://purl.org/vocabularies/princeton/wn30/synset-Roman_alphabet-noun-1')
        >>> reader.resolve_node('<http://purl.org/vocabularies/princeton/wn30/>')
        ('URL', 'http://purl.org/vocabularies/princeton/wn30/')
        >>> reader.resolve_node('"Abelian group"@en-us')
        ('en', 'Abelian group')
        """
        if node_text.startswith('<') and node_text.endswith('>'):
            # This is a literal URL, so decode_url will handle it directly.
            return 'URL', decode_url(node_text)
        elif node_text.startswith('"'):
            if '"^^' in node_text:
                quoted_string, type_tag = node_text.rsplit('^^', 1)
                type_tag = resource_name(decode_url(type_tag))
                assert (quoted_string.startswith('"') and quoted_string.endswith('"')), quoted_string
                return type_tag, decode_escapes(quoted_string[1:-1])
            elif '"@' in node_text:
                quoted_string, lang_code = node_text.rsplit('@', 1)
                assert (quoted_string.startswith('"') and quoted_string.endswith('"')), quoted_string
                lang = langcodes.get(lang_code).language
                return lang, decode_escapes(quoted_string[1:-1])
            elif node_text.endswith('"'):
                return 'en', decode_escapes(node_text[1:-1])
            else:
                raise ValueError("Can't understand value: %s" % node_text)
        elif ':' in node_text:
            prefix, resource = node_text.split(':', 1)
            if prefix not in self.prefixes:
                raise KeyError("Unknown prefix: %r" % prefix)
            url_base = self.prefixes[prefix]
            return 'URL', decode_url(url_base + resource)
        else:
            return (None, decode_escapes(node_text))


NQUADS_ITEM_RE = re.compile(r'''
    ( <                         # A URI/IRI enclosed in angle brackets
        (?P<uri> [^> ]+)
      >
    | "                         # A double-quoted string
      (?P<text>                 # If the string contains quotation marks,
        (\\"|[^"])+             # they must be escaped
      )
      "
      ( @(?P<lang> [A-Za-z_]+)  # The string can be tagged with a language code
      | ^^<(?P<type> [^> ]+)>   # Or a type
      )?                        # Or neither
    )
    ''', re.VERBOSE)


def parse_nquads_line(line):
    items = []
    for match in NQUADS_ITEM_RE.finditer(line):
        item = {}
        for group in ['uri', 'text', 'lang', 'type']:
            matched = match.group(group)
            if matched is not None:
                item[group] = matched
        if 'uri' in item:
            item['uri'] = decode_url(item['uri'])
        if 'lang' in item:
            item['lang'] = langcodes.standardize_tag(item['lang'])
        if 'type' in item:
            item['type'] = decode_url(item['type'])
        if 'text' in item:
            item['text'] = decode_escapes(item['text'])
        items.append(item)
    if len(items) == 3:
        items.append({})
    assert len(items) == 4
    return items


def parse_nquads(stream):
    for line in stream:
        line = line.strip()
        if line:
            yield parse_nquads_line(line)


class ExternalReferenceWriter:
    def __init__(self, filename):
        self.stream = open(filename, 'w', encoding='utf-8')
        self.seen = set()

    def write_link(self, conceptnet_uri, external_uri):
        """
        Record in a tab-separated file the fact that `conceptnet_uri` is
        the representation in ConceptNet of `external_uri`.
        """
        pair = (conceptnet_uri, external_uri)
        if pair not in self.seen:
            self.seen.add(pair)
            print('{}\t{}'.format(conceptnet_uri, external_uri), file=self.stream)

    def close(self):
        self.stream.close()
