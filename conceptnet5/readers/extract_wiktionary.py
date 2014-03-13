#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# A work in progress on a better first step for reading Wiktionary.
# Right now it puts its results into a bunch of files under "./en.wiktionary.org".
#
# TODO: when extracting links, try to determine what language they're in. It's
# annoying because it differs by section, and even by template:
#   {{sl-adv|head=[[na]] [[primer]]}}\n\n# [[for example]]

from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
import re
import os
import unicodedata
import json
from ftfy import ftfy
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SECTION_HEADER_RES = {}
for level in range(2, 8):
    equals = '=' * level
    regex = re.compile(
        r'''
        ^{equals}            # N equals signs, after start or newline
        \s*                  # There might be whitespace around the section title
        ([^=]+?)             # The section title, with no more = signs
        \s*
        {equals}\s           # End with N more equals signs and whitespace
        '''.format(equals=equals),
        # This is a verbose regex (ignore spaces and comments); this is a
        # multiline regex (the ^ should match any line start as well as the
        # start of the string)
        re.VERBOSE | re.MULTILINE
    )
    SECTION_HEADER_RES[level] = regex

# Match wikilinks. Deliberately fail to match links with colons in them,
# because those tend to be internal bookkeeping, or inter-wiki links of the
# non-translation kind.
#
# The match result contains two-item tuples, of which the first item is the
# link target.
WIKILINK_RE = re.compile(
    r'''
    \[\[                  # Wiki links begin with two left brackets.
    (                     # Match the link target:
        [^\[\]\|\{\}:]    #   The target doesn't contain other link syntax.
                          #   (We also don't like links with colons.)
    +?)                   # Match this part as tightly as possible.
    (                     # There might be a separate text to display:
        \|                #   It's separated by a vertical bar.
        [^\[\]]+          #   After that, there are non-bracket characters.
    )?                    # But this part is optional.
    \]\]                  # Finally, end with two right brackets.
    ''', re.VERBOSE
)
TRANSLATION_RE = re.compile(
    r'''
    \{\{                  # Translation templates start with two left braces.
    t.?.?                 # The template name is 1-3 chars starting with 't'.
    \|                    # A vertical bar terminates the template name.
    ([a-z]+)              # The first parameter is the language code. Match it.
    \|
    (.+?)                 # The second parameter is the target word. Match it.
    (?:                   # Throw away the following match:
        \|                #   There might be more parameters. It might be the
    |   \}\}              #   end of the template. We don't actually care. So
    )                     #   match a vertical bar or two right braces.
    ''', re.VERBOSE
)

TRANS_DIVIDER_RE = re.compile(
    r'''
    \{\{ 
    (check)?trans-       # Template names start with 'trans-' or 'checktrans-'.
    (top|bottom)         # We care when they're 'top' or 'bottom'.
    (
      \|(.*?)            # The template might take an optional parameter.
    )?
    \}\}                 # End with two right braces.
    ''', re.VERBOSE
)

SENSE_RE = re.compile(r'\{\{sense\|(.*?)\}\}')

def safe_path_component(text):
    return text.replace('/', '_').replace(' ', '_').replace(':',
        '_').replace('!', '_')

def fix_heading(heading):
    return ftfy(heading).strip('[]')

def safe_path(origtitle):
    title = safe_path_component(ftfy(origtitle))
    
    if len(title) == 0:
        title = origtitle = u'_'

    if title.startswith(u'-') or title.startswith(u'.'):
        title = u'_' + title
    try:
        charname = safe_path_component(unicodedata.name(origtitle[0]))
    except ValueError:
        charname = u'UNKNOWN'
    category = charname.split('_')[0]

    # some ridiculous stuff to give every article a unique name that can be
    # stored on multiple file systems and tab-completed
    if len(origtitle) == 1:
        pieces = [u'single_character', category, charname + '.json']
    else:
        try:
            charname2 = safe_path_component(unicodedata.name(origtitle[1]))
        except ValueError:
            charname2 = u'UNKNOWN'
        text_to_encode = unicodedata.normalize("NFKD", safe_path_component(title[:64]))
        finalpart = text_to_encode.encode('punycode').rstrip('-')
        pieces = [charname, charname2, finalpart + '.json']
    path = u'/'.join(pieces)
    return path
    

class ExtractPages(ContentHandler):
    def __init__(self, callback):
        self.in_article = False
        self.in_title = False
        self.cur_title = ''
        self.callback = callback

    def startElement(self, name, attrs):
        if name == 'text':
            self.in_article = True
            self.cur_text = []
        elif name == 'title':
            self.in_title = True
            self.cur_title = ''

    def endElement(self, name):
        if name == 'text':
            self.in_article = False
        elif name == 'title':
            self.in_title = False
        elif name == 'page':
            self.callback(self.cur_title, ''.join(self.cur_text))
    
    def characters(self, text):
        if self.in_title:
            self.cur_title += text
        elif self.in_article:
            self.cur_text.append(text)
            if len(self.cur_text) > 100000:
                # bail out
                self.in_article = False

def handle_page(title, text, site='en.wiktionary.org'):
    if ':' not in title:
        found = SECTION_HEADER_RES[2].split(text)
        headings = found[1::2]
        texts = found[2::2]
        for heading, text in zip(headings, texts):
            heading = fix_heading(heading)
            handle_language_section(site, title, heading, text)

def handle_language_section(site, title, heading, text):
    path = u'/'.join([site, safe_path_component(heading), safe_path(title)]).encode('utf-8')
    try:
        os.makedirs(os.path.dirname(path))
    except OSError:
        pass
    sec_data = handle_section(text, heading, level=2)
    data = {
        'site': site,
        'language': sec_data['heading'],
        'title': title,
        'sections': sec_data['sections']
    }
    jsondata = json.dumps(data, ensure_ascii=False, indent=2)
    out = open(path, 'w')
    out.write(jsondata.encode('utf-8'))
    out.close()
    

def handle_section(text, heading, level):
    section_finder = SECTION_HEADER_RES[level + 1]
    found = section_finder.split(text)
    headings = found[1::2]
    texts = found[2::2]
    data = {
        'heading': heading,
        'text': found[0].strip(),
        'sections': [handle_section(text2, heading2, level + 1)
                     for (text2, heading2) in zip(texts, headings)]
    }
    if heading == 'Translations':
        data['translations'] = extract_translations(found[0])
    else:
        data['links'] = parse_links(found[0])
        #data['sense'] = find_sense(found[0])
    return data


def parse_links(text):
    return [found[0] for found in WIKILINK_RE.findall(text)]


def extract_translations(text):
    translations = []
    pos = 0
    disambig = None
    in_trans_block = False
    while True:
        # Find whether the next relevant template tag is an individual
        # translation, or a divider between translation sections
        translation_match = TRANSLATION_RE.search(text, pos)
        divider_match = TRANS_DIVIDER_RE.search(text, pos)
        use_translation_match = None
        use_divider_match = None
        if translation_match is not None:
            if divider_match is not None:
                if translation_match.start() < divider_match.start():
                    use_translation_match = translation_match
                else:
                    use_divider_match = divider_match
            else:
                use_translation_match = translation_match
        else:
            use_divider_match = divider_match

        if use_divider_match is not None:
            match = use_divider_match
            pos = match.end()
            tagtype = match.group(2)
            if tagtype == 'top':
                if in_trans_block:
                    logger.warn(
                        u'starting a new trans block on top of an old one: '
                        u'\n%s' % text
                    )
                in_trans_block = True
                disambig = match.group(4)
            elif tagtype == 'bottom':
                in_trans_block = False
                disambig = None

        elif use_translation_match is not None:
            match = use_translation_match
            pos = match.end()
            translations.append({
                'langcode': match.group(1),
                'word': match.group(2),
                'disambig': disambig
            })
        else:
            return translations


def parse_wiktionary_file(filename):
    # Create a parser
    parser = make_parser()

    # Tell the parser we are not interested in XML namespaces
    parser.setFeature(feature_namespaces, 0)

    # Create the handler
    dh = ExtractPages(handle_page)

    # Tell the parser to use our handler
    parser.setContentHandler(dh)

    # Parse the input
    parser.parse(open(filename))

if __name__ == '__main__':
    parse_wiktionary_file('../../data/raw/wiktionary/enwiktionary.xml')
