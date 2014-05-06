#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

"""
Takes in a Wiktionary XML file, and outputs a JSON stream (.jsons) of objects
that split the entries into sections. Each language section is a top-level
object, and it contains objects for the subsections within it.
"""

from xml.sax import ContentHandler, make_parser
from xml.sax.handler import feature_namespaces
import re
import logging
from ftfy import ftfy
from conceptnet5.formats.json_stream import JSONStreamWriter
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

def fix_heading(heading):
    return ftfy(heading).strip('[]')

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

class WiktionaryWriter(object):
    def __init__(self, output_dir, nfiles=20):
        self.nfiles = nfiles
        self.writers = [
            JSONStreamWriter(output_dir + '/wiktionary_%02d.jsons' % i)
            for i in range(nfiles)
        ]

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
        parser.parse(open(filename))

    def handle_page(self, title, text, site='en.wiktionary.org'):
        if ':' not in title:
            found = SECTION_HEADER_RES[2].split(text)
            headings = found[1::2]
            texts = found[2::2]
            for heading, text in zip(headings, texts):
                heading = fix_heading(heading)
                self.handle_language_section(site, title, heading, text)

    def handle_language_section(self, site, title, heading, text):
        sec_data = self.handle_section(text, heading, level=2)
        data = {
            'site': site,
            'language': sec_data['heading'],
            'title': title,
            'sections': sec_data['sections']
        }
        filenum = hash((site, title, heading)) % self.nfiles
        self.writers[filenum].write(data)
        
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


def handle_file(input_file, output_dir):
    writer = WiktionaryWriter(output_dir)
    writer.parse_wiktionary_file(input_file)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input', help="English Wiktionary XML file")
    parser.add_argument('output', help='Directory to output to')
    args = parser.parse_args()
    handle_file(args.input, args.output)
