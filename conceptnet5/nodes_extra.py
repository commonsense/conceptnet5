import re

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


