"""
This file provides functions that can be called from Jinja templates, in order
to put together the text on the browsable ConceptNet site.
"""

from jinja2.ext import Markup

from conceptnet5.languages import get_language_name
from conceptnet5.uri import split_uri, uri_prefix

from .json_rendering import highlight_and_link_json


def describe_term_language(lang):
    """
    Take in a language code for a ConceptNet term, and output an English
    phrase describing its language, such as 'A French term' or 'An English
    term'.
    """
    language_name = get_language_name(lang)
    if language_name[0] in 'AEIOU' and not language_name.startswith('Uk'):
        article = 'An'
    else:
        article = 'A'

    content = '{article} <a href="/c/{lang}">{language_name}</a> term'.format(
        article=article, lang=lang, language_name=language_name
    )
    return Markup(content)


def full_language_name(term):
    """
    Get the English name of a language.

    One place this text is used is for the title text when you hover over a
    language code. For external links, there will be a site name there instead
    of a language, so we support that here.
    """
    if 'language' not in term:
        return term.get('site', '')
    lang = term['language']
    return get_language_name(lang)


def source_link(url, name):
    """
    Link to a ConceptNet source with the provided link text.
    """
    return '<a href="{url}">{name}</a>'.format(url=url, name=name)


CONTRIBUTOR_NAME_MAP = {
    '/s/resource/verbosity': 'Verbosity players',
    '/s/resource/wordnet/rdf/3.1': 'Open Multilingual WordNet',
    '/s/resource/opencyc/2012': 'OpenCyc 2012',
    '/s/resource/jmdict/1.07': 'JMDict 1.07',
    '/s/resource/dbpedia/2015/en': 'DBPedia 2015',
    '/s/resource/wiktionary/de': 'German Wiktionary',
    '/s/resource/wiktionary/en': 'English Wiktionary',
    '/s/resource/wiktionary/fr': 'French Wiktionary',
    '/s/resource/cc_cedict/2017-10': 'CC-CEDICT 2017-10',
    '/s/resource/unicode/cldr/31': 'Unicode CLDR',
    '/s/resource/unicode/cldr/32': 'Unicode CLDR',
    '/s/resource/unicode/cldr/32.0.1': 'Unicode CLDR',
}


ERROR_NAME_MAP = {
    400: 'Bad request',
    404: 'Not found',
    429: 'Too many requests',
    500: 'Server error',
    503: 'This ConceptNet interface is unavailable',
}


def error_name(code):
    """
    Get the human-readable name of an HTTP error code.
    """
    return ERROR_NAME_MAP.get(code, code)


def oxford_comma(items):
    """
    Join a list of human-readable items, using the Oxford comma when appropriate.
    """
    if len(items) == 0:
        return ''
    elif len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return "{0} and {1}".format(*items)
    else:
        comma_sep = ', '.join(items[:-1])
        last = items[-1]
        return "{0}, and {1}".format(comma_sep, last)


MAX_INDIVIDUALS = 3
KYOTO_YAHOO_CREDIT = 'crowdsourcing by Kyoto University & Yahoo Japan Corporation'


def describe_sources(sources, specific=True):
    """
    Build a marked-up text phrase describing the sources of our data.

    If `specific` is True, sources with many known individual contributors
    will list up to MAX_INDIVIDUALS of those contributors. If False, only
    the source as a whole will be credited. specific=False is used for the
    credit at the top of a page.
    """
    omcs_contributors = []
    omcs_count = 0
    ptt_count = 0
    nadya_count = 0
    more_sources = set()

    for source in sources:
        if 'activity' in source and source['activity'] == '/s/activity/omcs/nadya.jp':
            nadya_count += 1
        elif 'activity' in source and source['activity'] == '/s/activity/kyoto_yahoo':
            more_sources.add(source_link(source['activity'], KYOTO_YAHOO_CREDIT))
        elif 'contributor' in source:
            contributor = source['contributor']
            prefix = uri_prefix(contributor, 3)
            if prefix == '/s/contributor/omcs':
                if len(omcs_contributors) < MAX_INDIVIDUALS:
                    name = split_uri(contributor)[-1]
                    omcs_contributors.append(source_link(contributor, name))
                omcs_count += 1
            elif prefix == '/s/contributor/petgame':
                ptt_count += 1
            elif contributor in CONTRIBUTOR_NAME_MAP:
                more_sources.add(
                    source_link(contributor, CONTRIBUTOR_NAME_MAP[contributor])
                )
            else:
                more_sources.add(source_link(contributor, contributor))

    source_chunks = []
    if omcs_contributors:
        if specific:
            if omcs_count > MAX_INDIVIDUALS:
                omcs_contributors.append("{} more".format(omcs_count - MAX_INDIVIDUALS))

            omcs_str = '<a href="/s/activity/omcs">Open Mind Common Sense</a> contributors {}'.format(
                oxford_comma(omcs_contributors)
            )
            source_chunks.append(omcs_str)
        else:
            source_chunks.append(
                '<a href="/s/activity/omcs">Open Mind Common Sense</a> contributors'
            )
    if ptt_count:
        if specific:
            if ptt_count == 1:
                count_str = "a player"
            else:
                count_str = "{} players".format(ptt_count)
            source_chunks.append(
                '{} of the <a href="/s/contributor/petgame">PTT Pet Game</a>'.format(
                    count_str
                )
            )
        else:
            source_chunks.append(
                'the <a href="/s/contributor/petgame">PTT Pet Game</a>'
            )

    if nadya_count:
        if specific:
            if nadya_count == 1:
                count_str = "a player"
            else:
                count_str = "{} players".format(nadya_count)
            source_chunks.append(
                '{} of <a href="/s/activity/omcs/nadya.jp">nadya.jp</a>'.format(
                    count_str
                )
            )
        else:
            source_chunks.append('<a href="/s/activity/omcs/nadya.jp">nadya.jp</a>')

    source_chunks.extend(sorted(more_sources))
    if len(source_chunks) == 1:
        source_markup = "<strong>Source:</strong> {}".format(source_chunks[0])
    else:
        source_markup = "<strong>Sources:</strong> {}".format(
            oxford_comma(source_chunks)
        )
    return Markup(source_markup)


def describe_sources_brief(sources):
    """
    Provide an easy way to call `describe_sources()` with `specific=False` from
    a Jinja template.
    """
    return describe_sources(sources, False)


# Export functions that can be used in Jinja templates.
FILTERS = {
    'highlight_json': highlight_and_link_json,
    'describe_term_language': describe_term_language,
    'describe_sources': describe_sources,
    'describe_sources_brief': describe_sources_brief,
    'full_language_name': full_language_name,
    'error_name': error_name,
}
