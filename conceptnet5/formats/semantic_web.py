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


NQUADS_ITEM_RE = re.compile(r'''
    ( <                         # A URL (URI, IRI) enclosed in angle brackets
        (?P<url> [^> ]+)
      >
    | "                         # A double-quoted string
      (?P<text>                 # If the string contains quotation marks,
        (\\"|[^"])*             # they must be escaped
      )
      "
      ( @(?P<lang> [A-Za-z_]+)  # The string can be tagged with a language code
      | ^^<(?P<type> [^> ]+)>   # Or a type
      )?                        # Or neither
    | _:
      (?P<blank>[A-Za-z0-9_]+)  # A blank node identifier
    | [#] (?P<comment>.*)       # The line could end with a comment
    )\s*
    ''', re.VERBOSE)


def parse_nquads_line(line):
    items = []
    for match in NQUADS_ITEM_RE.finditer(line):
        item = {}
        for group in ['url', 'text', 'lang', 'type', 'blank', 'comment']:
            matched = match.group(group)
            if matched is not None:
                item[group] = matched
        if 'comment' in item:
            continue
        if 'url' in item:
            item['url'] = decode_url(item['url'])
        if 'lang' in item:
            item['lang'] = langcodes.standardize_tag(item['lang'])
        if 'type' in item:
            item['type'] = decode_url(item['type'])
        if 'text' in item:
            item['text'] = decode_escapes(item['text'])
        if item:
            items.append(item)
    if len(items) == 3:
        items.append({})
    # The line is either empty aside from comments, or contains a quad
    assert len(items) == 0 or len(items) == 4, line
    return items


def parse_nquads(stream):
    for line in stream:
        line = line.strip()
        if line:
            quad = parse_nquads_line(line)
            if quad:
                yield quad


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
