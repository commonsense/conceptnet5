# coding: utf-8
from __future__ import unicode_literals
from conceptnet5.wiktparse.parser import wiktionaryParser, wiktionarySemantics
from pprint import pprint
from collections import defaultdict

string_type = type('')


class LinkedText(object):
    """
    A LinkedText instance represents a partial parse result.

    It may contain a plain text representation, stored in `self.text`, indicating
    how this structure would be read when it is rendered in a Wiktionary entry.
    This form will be used when this result is used in a larger piece of text
    such as a definition.

    It also may contain structured data derived from the links and templates
    in the text, which is a list of EdgeInfo objects stored in `self.links`.

    Sometimes we don't care what text a given expression renders as, and we're
    only extracting information from its links. In that case, `self.text` should
    be the empty string.
    """
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
    """
    An EdgeInfo object keeps track of information that may eventually be used
    in a ConceptNet edge. Any of its fields may be None, and in some cases may
    be filled in later.

    For example, a translation template for the word "water" may give us the
    following EdgeInfo:

        EdgeInfo(language='es', target='agua', rel='TranslationOf')

    The translation corresponds to a particular sense of the English word
    'water', but that's indicated by a different template that groups together
    many translations of the same sense, which is higher up the parse tree.
    When we get there, we'll fill in `self.sense` with that information.

    The fields of an EdgeInfo object are:

    - `language`: the language that the *target* word is in
    - `target`: the spelling of the target word
    - `sense`: the word sense of the *source* word that this applies to
    - `rel`: The relation between the source and target words, as a string
      such as "TranslationOf" or "DerivedFrom"

    We don't represent the source word and its language here, because those
    are global to the Wiktionary entry we're parsing. We also don't represent
    the word sense of the target word, because we never know what it is.
    """
    def __init__(self, language, target, sense=None, rel=None):
        self.language = language
        self.target = target
        self.sense = sense
        self.rel = rel

    def set_language(self, language):
        return EdgeInfo(language, self.target, self.sense, self.rel)

    def set_target(self, target):
        return EdgeInfo(self.language, target, self.sense, self.rel)

    def set_sense(self, sense):
        return EdgeInfo(self.language, self.target, sense, self.rel)

    def set_rel(self, rel):
        return EdgeInfo(self.language, self.target, self.sense, rel)

    def __repr__(self):
        return "EdgeInfo(%r, %r, %r, %r)" % (
            self.language, self.target, self.sense, self.rel
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
        """
        Parse `text` starting from the given `rule_name`, applying these
        semantics to the resulting parse tree.
        """
        parser = wiktionaryParser()
        return parser.parse(text, whitespace='', rule_name=rule_name,
                            semantics=self, **kwargs)

    def wikitext(self, ast):
        """
        The 'wikitext' rule parses arbitrary text that may include markup,
        and returns a LinkedText instance. More restrictive versions of this
        are `one_line_wikitext`, `text_with_links`, `one_line_text_with_links`,
        and `linktext` (which is used in parsing external links).

        Parse rules:

            one_line_text = @term | comment | html_tag | @colon | @equals
                            | @single_left_bracket | @single_right_bracket
                            | @single_left_brace | @single_right_brace | @SP ;
            text = @NL | @one_line_text ;
            text_with_links = { wiki_link | text }+ ;
            one_line_text_with_links = { wiki_link | one_line_text }+ ;
            linktext = { @+:term | html_tag | NL | @+:colon | @+:equals }+ ;
            one_line_wikitext = { template | wiki_link | external_link | one_line_text }+ ;
            wikitext = { template | wiki_link | external_link | text }+ ;
        """
        # FIXME: This might be quite inefficient. We throw away a lot of
        # wikitext, so maybe we should not try to interpret its semantics
        # yet, or maybe we should have an "ignored_wikitext" rule with no
        # semantics.
        return join_text(ast)
    linktext = one_line_text_with_links = text_with_links = one_line_wikitext = wikitext

    def wiki_link(self, ast):
        """
        A `wiki_link` is a link in double brackets, such as [[target]], [[target|text]],
        or [[site:target|text]].

        Parse rule:

            wiki_link = left_brackets [ site:term colon ] target:term [ vertical_bar text:term ] right_brackets ;
        """
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
                target=target
            )]
        text = ast['text'] or ast['target']
        return LinkedText(text=text, links=links)

    def external_link(self, ast):
        """
        External links contain a complete URL, probably followed by the title
        of the link, such as:

            [http://www.americanscientist.org/authors/detail/david-van-tassel David Van Tassel]

        Parse rules:

            urlpath = ?/[^ \[\]{}<>|]+/? ;
            url = schema:term colon path:urlpath ;
            external_link = left_bracket url:url WS [ text:linktext ] right_bracket ;
        """
        # Keep only the text of external links
        return LinkedText(text=ast['text'], links=[])

    def template_args(self, ast):
        """
        Template args look like:

            |arg1|arg2|name1=val1|name2=val2

        The `template_args` rule gets a list of values that are either
        positional or keyword arguments. We turn them into a dictionary,
        where the positional arguments get keys that are integers starting
        from 1.

        Parse rules:

            named_arg = key:term WS equals WS value:wikitext ;
            template_arg = [ named:named_arg | positional:wikitext ] ;
            template_args = { WS vertical_bar WS @+:template_arg }+ ;
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
        A simple template looks like this:

            {{archaic}}

        More complex templates take arguments, such as this translation into French:

            {{t+|fr|exemple|m}}

        And very complex templates can have both positional and named arguments:

            {{t|ja|例え|tr=[[たとえ]], tatoe}}

        When we parse a complete template, with a template name and args --
        which is not the case when we know we're looking for a specific
        template -- add its name as argument 0.

        Parse rule:

            template = left_braces WS name:term [args:template_args] right_braces ;
        """
        if ast['args'] is not None:
            template_value = ast['args'].copy()
        else:
            template_value = {}
        template_value[0] = ast['name']
        return template_value

    def translation_template(self, ast):
        """
        This rule handles templates that indicate a translation, returning an EdgeInfo.

        Parse rules:

            translation_name = "t-simple" | "t+" | "t" | "t-" | "t0" | "tø" ;
            translation_template = left_braces WS translation_name @template_args right_braces ;
        """
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
        """
        Lines in the translation section begin with an asterisk as a bullet,
        then may contain translation templates interspersed with plain text.
        We want to get just the values of the translation templates.

        Parse rules:

            translation_entry = bullet SP { translations+:translation_template | one_line_text_with_links }+ NL ;
        """
        if isinstance(ast, list):
            # If there were no translations found, we end up with a list
            # of all the other junk.
            return []
        if ast['translations'] is None:
            return []
        return ast['translations']

    def translation_content(self, ast):
        """
        Parse rule:

            translation_content = { trans_mid_template | entries+:translation_entry | WS }+ ;
        """
        if ast['entries'] is None:
            return []
        return sum(ast['entries'], [])

    def translation_block(self, ast):
        """
        Parse a block of translations, which may be grouped together into a
        word sense. Set that sense (which may be None) as the sense for all
        the translations.
        """
        sense = ast['top']['sense']
        return [info.set_sense(sense) for info in ast['translations']]

    def translation_section(self, ast):
        return ast

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

    def etyl_template_and_link(self, ast):
        language = ast['etyl']['language']
        links = [link.set_language(language)
                 for link in ast['link'].links]
        return LinkedText(text=ast['link'].text, links=links)

    def link_entry(self, ast):
        """
        Parse rules:

            sense_template = left_braces WS "sense" WS vertical_bar @text_with_links right_braces ;
            link_entry = bullet SP [sense:sense_template] SP { link+:link_template | link+:wiki_link | template | external_link | one_line_text }+ NL >> ;
        """
        if ast['links'] is None:
            return []

        sense = ast['sense']
        links = []
        for sub_links in ast['links']:
            links.extend(sub_links.links)

        if sense is not None:
            links = [link.set_sense(sense) for link in links]

        return links

    def sense_template(self, ast):
        return ast.text

    def link_section(self, ast):
        """
        Parse rule:

            link_section = { entries+:link_entry | template | WS }+ ;
        """
        return sum(ast['entries'] or [], [])

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
