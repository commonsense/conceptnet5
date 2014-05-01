from __future__ import unicode_literals
from conceptnet5.wiktparse.parser import wiktionaryParser, wiktionarySemantics
from pprint import pprint
from collections import defaultdict

string_type = type('')


class LinkedText(object):
    def __init__(self, text, links):
        if isinstance(text, LinkedText):
            self.text = text.text
            self.links = text.links + links
        else:
            self.text = text
            self.links = links

    def __add__(self, other):
        text = self.text + ' ' + other.text
        links = self.links + other.links
        return LinkedText(text, links)

    def __repr__(self):
        return "LinkedText(%r, %r)" % (self.text, self.links)


class EdgeInfo(object):
    def __init__(self, language, target, pos=None, sense=None, rel=None):
        self.language = language
        self.target = target
        self.pos = pos
        self.sense = sense
        self.rel = rel

    def set_language(self, language):
        return EdgeInfo(language, self.target, self.pos, self.sense, self.rel)

    def set_pos(self, pos):
        return EdgeInfo(self.language, self.target, pos, self.sense, self.rel)

    def set_sense(self, sense):
        return EdgeInfo(self.language, self.target, self.pos, sense, self.rel)

    def set_rel(self, rel):
        return EdgeInfo(self.language, self.target, self.pos, self.sense, rel)

    def __repr__(self):
        return "EdgeInfo(%r, %r, %r, %r, %r)" % (
            self.language, self.target, self.pos, self.sense, self.rel
        )


def join_text(lst):
    if lst is None:
        return None

    texts = []
    links = []
    for item in lst:
        if item is None:
            pass
        elif isinstance(item, string_type):
            texts.append(item)
        elif isinstance(item, LinkedText):
            if item.text is not None:
                texts.append(item.text)
            links.extend(item.links)
        elif isinstance(item, dict):
            # This is an unhandled template; we ignore it for the purpose of
            # extracting text
            pass
        else:
            raise TypeError(item)

    text = ''.join(texts)
    return LinkedText(text, links)


class ConceptNetWiktionarySemantics(wiktionarySemantics):
    def __init__(self, language, **kwargs):
        self.default_language = language
        wiktionarySemantics.__init__(self, **kwargs)

    def parse(self, text, rule_name, **kwargs):
        parser = wiktionaryParser()
        return parser.parse(text, whitespace='', rule_name=rule_name,
                            semantics=self, **kwargs)

    def linktext(self, ast):
        assert isinstance(ast, list)
        return join_text(ast)
    
    def wikitext(self, ast):
        # FIXME: This might be quite inefficient. We throw away a lot of
        # wikitext, so maybe we should not try to interpret its semantics
        # yet, or maybe we should have an "ignored_wikitext" rule with no
        # semantics.
        value = join_text(ast)
        return value
    one_line_wikitext = wikitext

    def wiki_link(self, ast):
        if ast['site'] is not None:
            # We don't like off-Wiktionary links
            links = []
        else:
            # Some entries specify their language using a hash-reference to
            # that language's section of the page.
            #
            # TODO: Does anyone ever, for example, link to the French
            # definition of the same surface word with a link that just says
            # [[#French]]? What text even shows up in that case? How do we
            # figure out what the name of the current entry is, so we can
            # point to it?
            language = self.default_language
            target = ast['target']
            if target.startswith('#'):
                language = ast['target'][1:]
                target = ast['text']
            links = [EdgeInfo(
                language=language,
                target=ast['target']
            )]
        text = ast['text'] or ast['target']
        return LinkedText(text=text, links=links)

    def external_link(self, ast):
        # Keep only the text of external links
        return LinkedText(text=ast['text'], links=[])

    def etyl_template_and_link(self, ast):
        language = ast['etyl']['language']
        links = [link.set_language(language)
                 for link in ast['link'].links]
        return LinkedText(text=ast['link'].text, links=links)
    
    def link_template(self, ast):
        # This is going to be complicated. We need to figure out the
        # argument structure of many different templates.
        args = defaultdict(lambda: None)
        links = []
        
        # Extract the text values of all arguments, and collect their links
        # if they happen to have any
        for key, value in ast['args'].items():
            if value is not None:
                args[key] = value.text
                links.extend(value.links)

        text = ''

        linktype = ast['linktype']
        if linktype == 'l' and ast['subtypes']:
            language = ast['subtypes'][0]
            target = args[1]
            links = [EdgeInfo(language=language, target=target)]
            text = target
        
        elif linktype in ('l', 'term/t'):
            language = args[1]
            target = args[2]
            text = args[3] or target
            links = [EdgeInfo(language=language, target=target)]
        
        elif linktype == 'term':
            # {{term}} without a language really is in an unspecified language.
            language = args['lang']
            target = args[1]
            text = args[2] or target
            if text == 'byspel':
                assert language is not None, ast
            links = [EdgeInfo(language=language, target=target, rel='DerivedFrom')]

        elif linktype == 'ja-l':
            language = 'ja'
            text = target = args[1]
            links = [EdgeInfo(language=language, target=target)]
        
        elif linktype == 'ko-inline':
            language = 'ko'
            text = target = args[1]
            links = [EdgeInfo(language=language, target=target)]
        
        # Cases below here don't need to set 'text', because they're only used
        # in etymologies
        elif linktype in ('back-form', 'clipping', '-er',):
            language = args['lang'] or self.default_language
            links = [EdgeInfo(language=language, target=args[1], rel='DerivedFrom')]
        
        elif linktype in ('borrowing'):
            links = [EdgeInfo(language=args[1], target=args[2], rel='DerivedFrom')]
        
        elif linktype in ('blend', 'calque', 'compound', 'confix', 'prefix', 'suffix'):
            # TODO: 'calque' has extra parameters, 'etyl lang' and 'etyl term',
            # providing the link to the language being calqued from
            language = args['lang'] or self.default_language
            links = [
                EdgeInfo(language=language, target=args[1], rel='DerivedFrom'),
                EdgeInfo(language=language, target=args[2], rel='DerivedFrom')
            ]
            if args[3]:
                links.append(EdgeInfo(language=language, target=args[3], rel='DerivedFrom'))

        elif linktype == 'etycomp':
            # Complex compound word etymologies
            lang1 = args['lang1'] or self.default_language
            lang2 = args['lang2'] or args['lang1'] or self.default_language
            links = [
                EdgeInfo(language=lang1, target=args[1], rel='DerivedFrom'),
                EdgeInfo(language=lang2, target=args[2], rel='DerivedFrom')
            ]

        return LinkedText(text=text, links=links)


    def template_args(self, ast):
        """
        The `template_args` rule gets a list of values that are either
        positional or keyword arguments. We turn them into a dictionary,
        where the positional arguments get keys that are integers starting
        from 1.
        """
        template_value = {}
        position = 1
        for item in ast:
            if item['named']:
                key = item['named']['key']
                value = item['named']['value']
            else:
                key = position
                position += 1
                value = item['positional']
            template_value[key] = value
        return template_value

    def template(self, ast):
        """
        When we parse a complete template, with a template name and args --
        which is not the case when we know we're looking for a specific
        template -- add its name as argument 0.
        """
        if ast['args'] is not None:
            template_value = ast['args'].copy()
        else:
            template_value = {}
        template_value[0] = ast['name']
        return template_value

    def translation_template(self, ast):
        return EdgeInfo(
            language=ast[1].text,
            target=ast[2].text,
            rel='TranslationOf'
        )

    def sensetrans_top_template(self, ast):
        # FIXME: This might be the identity
        return {'sense': ast['sense']}

    def checktrans_top_template(self, ast):
        return {'sense': None}

    def translation_entry(self, ast):
        if isinstance(ast, list):
            # If there were no translations found, we end up with a list
            # of all the other junk.
            return []
        if ast['translations'] is None:
            return []
        return ast['translations']
    
    def translation_block(self, ast):
        sense = ast['top']['sense']
        return [info.set_sense(sense) for info in sum(ast['translations'], [])]

    def translation_section(self, ast):
        return ast


def main(filename, startrule, trace=False):
    with open(filename) as f:
        text = f.read()
    semantics = ConceptNetWiktionarySemantics(language='en')
    ast = semantics.parse(
        text,
        startrule,
        filename=filename,
        trace=trace
    )
    pprint(ast)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Semantic parser for wiktionary.")
    parser.add_argument('-t', '--trace', action='store_true',
                        help="output trace information")
    parser.add_argument('file', metavar="FILE", help="the input file to parse")
    parser.add_argument('startrule', metavar="STARTRULE",
                        help="the start rule for parsing")
    args = parser.parse_args()

    main(args.file, args.startrule, trace=args.trace)
