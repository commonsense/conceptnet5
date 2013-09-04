# -*- coding: utf-8 -*-

import re
import ftfy
from metanl import english
from metanl.general import preprocess_text

JAPANESE_PARTS_OF_SPEECH = {
    u'名詞': u'n',
    u'副詞': u'r',
    u'形容詞': u'a',
    u'動詞': u'v',
}

def handle_disambig(text):
    """
    Get a canonical representation of a Wikipedia topic, which may include
    a disambiguation string in parentheses.

    Returns (name, disambig), where "name" is the topic name,
    and "disambig" is a string corresponding to the disambiguation text or
    None.
    """
    # find titles of the form Foo (bar)
    text = text.replace('_', ' ').replace('/', ' ')
    while '  ' in text:
        text = text.replace('  ', ' ')
    match = re.match(r'([^(]+) \((.+)\)', text)
    if not match:
        return text, None
    else:
        return match.group(1), 'n/' + match.group(2).strip(' _')

def make_concept_uri(text, lang, disambiguation=None):
    text = ftfy.ftfy(text).strip()
    if disambiguation is None:
        text, disambiguation = handle_disambig(text)
    if disambiguation is not None:
        if isinstance(disambiguation, str):
            disambiguation = disambiguation.decode('utf-8')
        disambiguation = ftfy.ftfy(disambiguation)

    if lang == 'en':
        normalized = english.normalize(text)
    elif lang == 'ja' and disambiguation is not None:
        match = re.search(r'\((.*?)\)', disambiguation)
        if match:
            parenthesized = match.group(1)
            pos, rest = disambiguation.split('/', 1)
            if parenthesized in JAPANESE_PARTS_OF_SPEECH:
                pos = JAPANESE_PARTS_OF_SPEECH[parenthesized]
            else:
                pos = 'n'
            disambiguation = pos + '/' + re.sub(r'\s*\((.*?)\)\s*', '', rest)
        normalized = preprocess_text(text).lower()
    else:
        normalized = preprocess_text(text).lower()

    if disambiguation is not None:
        disambiguation = disambiguation.strip().replace(' ', '_').lower()
    if disambiguation:
        return '/c/%s/%s/%s' % (lang, normalized.replace(' ', '_'), disambiguation)
    else:
        return '/c/%s/%s' % (lang, normalized.replace(' ', '_'))

def list_to_uri_piece(lst):
    """
    Encode a list in a format that is hierarchical yet fits into a URI.

    args:
    lst -- the list which will be encoded

    """
    out_tokens = [u'[/']
    first = True
    for item in lst:
        if first:
            first = False
        else:
            out_tokens.append(u'/,/')
        out_tokens.append(item.strip('/'))
    out_tokens.append(u'/]')
    return u''.join(out_tokens)

def uri_piece_to_list(uri):
    """
    Undo the effect of `list_to_uri_piece`.

    args:
    uri -- the uri to be decoded into a list
    """
    pieces = uri.split(u'/')
    assert pieces[0] == '['
    assert pieces[-1] == ']'
    chunks = []
    current = []
    depth = 0
    for piece in pieces[1:-1]:
        if piece == u',' and depth == 0:
            chunks.append('/' + '/'.join(current))
            current = []
        else:
            current.append(piece)
            if piece == '[':
                depth += 1
            elif piece == ']':
                depth -= 1
    chunks.append('/' + '/'.join(current))
    return chunks

def make_assertion_uri(relation_uri, arg_uri_list, short=False):
    """
    creates assertion uri out of component uris
    
    args:
    relation_uri -- the uri of the relation being used i.e 'rel/IsA' or 'en/eat'
    arg_uri_list -- the uris (in list form) of the arguments of the assertion
    i.e ['/en/dog',...]

    """
    if short:
        tag = 'a'
    else:
        tag = 'assertion'
    return make_list_uri(tag, [relation_uri]+arg_uri_list)
	    
def make_list_uri(_type, args):
    """
    Creates any list-based uri out of component uris
    
    args:
    _type -- the type of uri being made i.e assertion
    args -- the argument uris i.e ['/en/eat','/en/dog/',..]

    """
    arglist = list_to_uri_piece(args)
    return '/%s/%s' % (_type, arglist)

def make_operator_uri(sources, op='and'):
    sources = sorted(sources)
    assert len(sources) >= 1
    if len(sources) == 1:
        return sources[0]
    else:
        return [make_list_uri(op, sources)]

def make_conjunction_uri(sources):
    return make_operator_uri(sources, 'and')

def make_disjunction_uri(sources):
    return make_operator_uri(sources, 'or')

def make_and_or_tree(list_of_lists):
    ands = [make_conjunction_uri(sublist) for sublist in list_of_lists]
    if len(ands) == 1:
        return ands[0]
    else:
        tree = [make_list_uri('or', ands)]
        return tree

def normalize_uri(uri):
    """
    Ensure that a URI is in Unicode, strip whitespace that may have crept
    in, and change spaces to underscores, creating URIs that will be
    friendlier to work with later.

    We don't worry about URL-quoting here; the client framework takes
    care of that for us.

    args:
    uri -- the uri being normalized and returned
    """
    if isinstance(uri, str):
        uri = uri.decode('utf-8')
    return uri.strip().replace(u' ', u'_')

def concept_to_lemmas(concept):
    """
    Given a concept in lemmatized URI form, extract all the word roots
    that appear in it. This includes lemmatizing the disambiguation text,
    if it is there.
    """
    lemmas = []
    if concept.startswith('/c/'):
        parts = concept.split('/')
        lang = parts[2]
        if len(parts) > 3:
            # get the concept name
            lemmas.extend(parts[3].replace('_', ' ').split())
        if len(parts) > 5:
            uri = make_concept_uri(parts[5], lang)
            norm = uri.split('/')[3]
            lemmas.extend(norm.split('_'))
    return lemmas

