#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

"""
Takes in a Wiktionary XML file, and outputs msgpack streams of objects
that split the entries into sections. Each language section is a top-level
object, and it contains objects for the subsections within it.
"""

from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
import re
import logging
import langcodes
from ftfy import ftfy
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.formats.sql import TitleDBWriter
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

# Regex for sub-sections in the German wiktionary
SUB_SECTION_RE = re.compile(
    r'''
    ^{{          # double opening braces
    ([^\|}]+)    # the subsection title; must not contain vertical bars
    }}           # double closing brace
    \s+          # trailing space (likely just a newline)
    ''', re.VERBOSE | re.MULTILINE)

# To get the language (as the first capturing group) out of a string such as
# "Buch ({{Sprache|Deutsch}})" in the German witkionary
DE_LANGUAGE_RE = re.compile(r'{{[^\|}]+\|([^}]+)}}')
JA_LANGUAGE_RE = re.compile(r'\{\{([A-Za-z-]+)\}\}')


def fix_heading(heading):
    return ftfy(heading).strip('[]')


class ExtractPages(ContentHandler):
    def __init__(self, callback):
        self.in_base = False
        self.in_article = False
        self.in_title = False
        self.cur_title = ''
        self.site = None
        self.callback = callback

    def startElement(self, name, attrs):
        if name == 'base':
            self.in_base = True
            self.cur_text = []
        elif name == 'text':
            self.in_article = True
            self.cur_text = []
        elif name == 'title':
            self.in_title = True
            self.cur_title = ''

    def endElement(self, name):
        if name == 'base' and self.site is None:
            # Derive the site from the first base element encountered (presumed
            # to be a child of the siteinfo element)
            self.in_base = False
            self.site = self.cur_text[0].split('/')[2]
        if name == 'text':
            self.in_article = False
        elif name == 'title':
            self.in_title = False
        elif name == 'page':
            self.callback(self.cur_title, ''.join(self.cur_text), self.site)

    def characters(self, text):
        if self.in_title:
            self.cur_title += text
        elif self.in_article or self.in_base:
            self.cur_text.append(text)
            if len(self.cur_text) > 100000:
                # bail out
                self.in_article = False


def _language_name_to_code(name, name_language_code):
    try:
        found = langcodes.find_name('language', name, name_language_code)
        return str(found)
    except LookupError:
        return None


def _language_code_to_name(code):
    return langcodes.get(code).language_name('en')


class WiktionaryWriter(object):
    """
    Parses a wiktionary file in XML format and saves the results to a set of
    files in msgpack format and a SQLite database.

    Subclasses most likely want to override the methods `_get_language_code()`
    and `handle_section()`.
    """
    def __init__(self, output_dir, nfiles=20):
        self.nfiles = nfiles
        self.writers = [
            MsgpackStreamWriter(output_dir + '/wiktionary_%02d.msgpack' % i)
            for i in range(nfiles)
        ]
        self.title_db = TitleDBWriter(output_dir + '/titles.db', clear=True)

    def _get_language_code(self, language):
        return _language_name_to_code(language, 'en')

    def parse_wiktionary_file(self, filename):
        # Create a parser
        parser = make_parser()

        # Tell the parser we are not interested in XML namespaces
        parser.setFeature(feature_namespaces, 0)

        # Create the handler
        dh = ExtractPages(self.handle_page)

        # Tell the parser to use our handler
        parser.setContentHandler(dh)

        # Parse the input
        with self.title_db.transaction():
            parser.parse(open(filename))

    def handle_page(self, title, text, site):
        if ':' not in title:
            found = SECTION_HEADER_RES[2].split(text)
            headings = found[1::2]
            texts = found[2::2]
            for heading, text in zip(headings, texts):
                heading = fix_heading(heading)
                self.handle_language_section(site, title, heading, text)

    def handle_language_section(self, site, title, heading, text):
        sec_data = self.handle_section(text, heading, level=2)
        language = self._get_language_code(sec_data['heading'])
        if language is None:
            return
        data = {
            'site': site,
            'language': language,
            'title': title,
            'sections': sec_data['sections']
        }
        filenum = hash((site, title, heading)) % self.nfiles
        self.writers[filenum].write(data)

        # Save the languages and titles to a database file
        self.title_db.add(language, title.lower())

    def handle_section(self, text, heading, level):
        section_finder = SECTION_HEADER_RES[level + 1]
        found = section_finder.split(text)
        headings = found[1::2]
        texts = found[2::2]
        data = {
            'heading': heading,
            'text': found[0].strip(),
            'sections': [self.handle_section(text2, heading2, level + 1)
                         for (text2, heading2) in zip(texts, headings)]
        }
        return data

    def close(self):
        self.title_db.close()


class DeWiktionaryWriter(WiktionaryWriter):
    langcode = 'de'
    def _get_language_code(self, heading):
        lang_match = DE_LANGUAGE_RE.search(heading)
        if lang_match:
            name = lang_match.group(1).strip()
            return _language_name_to_code(name, 'de')
        else:
            return None

    def handle_section(self, text, heading, level=None):
        """
        Sections within a page of the German wiktionary are mostly enclosed in
        double braces ({{Bedeutungen}}, {{Synonyme}}, etc.), except for the
        translation sections, which are introduced by 4 equals signs:
        '==== Übersetzungen ===='.
        """
        sections = []
        # First handle translations
        sectioned = SECTION_HEADER_RES[4].split(text)
        if len(sectioned) > 1 and sectioned[1] == 'Übersetzungen':
            if len(SUB_SECTION_RE.split(sectioned[2])) == 1:
                sections.append({'heading': sectioned[1],
                                 'text': sectioned[2]})
        # Now handle the rest
        found = SUB_SECTION_RE.split(sectioned[0])
        headings = found[1::2]
        texts = found[2::2]
        for (hdg, txt) in zip(headings, texts):
            sections.append({'heading': hdg, 'text': txt.lstrip()})
        return {
            'heading': heading,
            'text': found[0].strip(),
            'sections': sections
        }


class JaWiktionaryWriter(WiktionaryWriter):
    langcode = 'ja'
    def _get_language_code(self, heading):
        match = JA_LANGUAGE_RE.match(heading)
        if match:
            return langcodes.standardize_tag(match.group(1))
        else:
            return None


LANGUAGE_TO_WRITER = {'en': WiktionaryWriter, 'de': DeWiktionaryWriter, 'ja': JaWiktionaryWriter}


def handle_file(input_file, output_dir, language, nfiles=20):
    """Utility method for unit testing. Primary difference from the main usage
    is that it sets the number of files to 1 to make retrieving the output
    more straightforward."""
    writer = LANGUAGE_TO_WRITER[language](output_dir, nfiles=nfiles)
    writer.parse_wiktionary_file(input_file)
    writer.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help="Wiktionary XML file")
    parser.add_argument('output', help='Directory to output to')
    parser.add_argument('-l', '--language',
                        choices=['de', 'en', 'ja'],
                        default='en',
                        help='Two-letter ISO language code of the input file')
    parser.add_argument('-n', '--nfiles', type=int, default=20,
                        help='Number of output files to create')

    args = parser.parse_args()

    handle_file(args.input, args.output, args.language, args.nfiles)
