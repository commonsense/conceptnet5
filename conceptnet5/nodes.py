def make_concept_uri(text, lang, disambiguation=None):
    if lang == 'en':
        from metanl import english
        normalized, disambig = english.normalize_topic(text)
    elif lang == 'ja':
        from metanl import japanese
        normalized, disambig = japanese.normalize(text), None
    elif lang in ('pt', 'hu', 'nl', 'es'):
        # languages where we know the stopword list
        import simplenlp
        nlp = simplenlp.get(lang)
        disambig = None
        normalized, disambig = nlp.normalize(text), None
    else:
        normalized = text
        disambig = None
    if disambiguation is not None:
        disambig = disambiguation.replace(' ', '_')
    if disambig:
        return '/c/%s/%s/%s' % (lang, normalized.replace(' ', '_'), disambig)
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

