from __future__ import unicode_literals, print_function
import re
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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


# The above functions were pulled out from `extract_wiktionary.py`, but they
# really belong here in the post-extraction step.
# TODO: actually do something with them.
