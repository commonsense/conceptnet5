from __future__ import unicode_literals
from conceptnet5.wiktparse.parser import wiktionaryParser, wiktionarySemantics
from pprint import pprint


string_type = type('')


class LinkedText(object):
    def __init__(self, text, links):
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


def join_text(lst, sep=' '):
    if lst is None:
        return None

    texts = []
    for item in lst:
        if item is None:
            pass
        elif isinstance(item, string_type):
            texts.append(item)
        elif isinstance(item, LinkedText):
            if item.text is not None:
                texts.append(item.text)
        else:
            raise TypeError(item)

    return sep.join(texts)


class ConceptNetWiktionarySemantics(wiktionarySemantics):
    def __init__(self, language, **kwargs):
        self.default_language = language
        wiktionarySemantics.__init__(self, **kwargs)

    def parse(self, text, rule_name, **kwargs):
        parser = wiktionaryParser()
        return parser.parse(text, rule_name=rule_name, semantics=self,
                            **kwargs)

    def wiki_link(self, ast):
        if 'site' in ast:
            # We don't like off-Wiktionary links
            links = []
        else:
            links = [EdgeInfo(
                language=self.default_language,
                target=ast['target']
            )]
        return LinkedText(text=ast['text'], links=links)

    def external_link(self, ast):
        # Keep only the text of external links
        return LinkedText(text=ast['text'], links=[])

    def link_template(self, ast):
        # This is going to be complicated. We need to figure out the
        # argument structure of many different templates.
        raise NotImplementedError

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
            if 'key' in item:
                key = item['key']
            else:
                key = position
                position += 1
            template_value[key] = join_text(item['value'])
        return template_value

    def template(self, ast):
        """
        When we parse a complete template, with a template name and args --
        which is not the case when we know we're looking for a specific
        template -- add its name as argument 0.
        """
        template_value = ast['args'].copy()
        template_value[0] = ast['name']
        return template_value

    def translation_template(self, ast):
        return EdgeInfo(
            language=ast[1],
            target=ast[2],
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
