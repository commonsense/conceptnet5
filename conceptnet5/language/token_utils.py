# coding: utf-8
from __future__ import unicode_literals
"""
This file contains some generally useful operations you would perform to
separate and join tokens. The tools apply most to English, but should also
be able to do their job in any Western language that uses spaces.
"""

import sys
import re

PY2 = (sys.version_info.major < 3)


def casefold(text):
    """
    Standardize the case of text by converting it to uppercase first, then to
    lowercase.
    """
    if hasattr(str, 'casefold'):
        return text.casefold()
    else:
        return text.upper().lower()


# Sorry for the mess. These are regular expressions for matching sequences
# of characters whose major Unicode category is not Z (whitespace), P
# (punctuation), S (symbols), or C (control characters). They are optimized
# by allowing them to merge adjacent ranges that are only separated by
# unassigned codepoints.
#
# The code that originally generated these expressions is in the `wordfreq`
# package.
#
# On Py2 we have to exclude characters outside the Basic Multilingual Plane
# from tokens, because these characters are handled inconsistently depending
# on how Python was compiled.
if PY2:
    TOKEN_RANGE = "[0-9A-Za-z\xaa-\xaa\xb2-\xb3\xb5-\xb5\xb9-\xba\xbc-\xbe\xc0-\xd6\xd8-\xf6\xf8-\u02c1\u02c6-\u02d1\u02e0-\u02e4\u02ec-\u02ec\u02ee-\u02ee\u0300-\u0374\u0376-\u037d\u0386-\u0386\u0388-\u03f5\u03f7-\u0481\u0483-\u0559\u0561-\u0587\u0591-\u05bd\u05bf-\u05bf\u05c1-\u05c2\u05c4-\u05c5\u05c7-\u05f2\u0610-\u061a\u0620-\u0669\u066e-\u06d3\u06d5-\u06dc\u06df-\u06e8\u06ea-\u06fc\u06ff-\u06ff\u0710-\u07f5\u07fa-\u082d\u0840-\u085b\u08a0-\u0963\u0966-\u096f\u0971-\u09f1\u09f4-\u09f9\u0a01-\u0aef\u0b01-\u0b6f\u0b71-\u0bf2\u0c01-\u0c7e\u0c82-\u0d75\u0d7a-\u0df3\u0e01-\u0e3a\u0e40-\u0e4e\u0e50-\u0e59\u0e81-\u0f00\u0f18-\u0f19\u0f20-\u0f33\u0f35-\u0f35\u0f37-\u0f37\u0f39-\u0f39\u0f3e-\u0f84\u0f86-\u0fbc\u0fc6-\u0fc6\u1000-\u1049\u1050-\u109d\u10a0-\u10fa\u10fc-\u135f\u1369-\u138f\u13a0-\u13f4\u1401-\u166c\u166f-\u167f\u1681-\u169a\u16a0-\u16ea\u16ee-\u1734\u1740-\u17d3\u17d7-\u17d7\u17dc-\u17f9\u180b-\u180d\u1810-\u193b\u1946-\u19da\u1a00-\u1a1b\u1a20-\u1a99\u1aa7-\u1aa7\u1b00-\u1b59\u1b6b-\u1b73\u1b80-\u1bf3\u1c00-\u1c37\u1c40-\u1c7d\u1cd0-\u1cd2\u1cd4-\u1fbc\u1fbe-\u1fbe\u1fc2-\u1fcc\u1fd0-\u1fdb\u1fe0-\u1fec\u1ff2-\u1ffc\u2070-\u2079\u207f-\u2089\u2090-\u209c\u20d0-\u20f0\u2102-\u2102\u2107-\u2107\u210a-\u2113\u2115-\u2115\u2119-\u211d\u2124-\u2124\u2126-\u2126\u2128-\u2128\u212a-\u212d\u212f-\u2139\u213c-\u213f\u2145-\u2149\u214e-\u214e\u2150-\u2189\u2460-\u249b\u24ea-\u24ff\u2776-\u2793\u2c00-\u2ce4\u2ceb-\u2cf3\u2cfd-\u2cfd\u2d00-\u2d6f\u2d7f-\u2dff\u2e2f-\u2e2f\u3005-\u3007\u3021-\u302f\u3031-\u3035\u3038-\u303c\u3041-\u309a\u309d-\u309f\u30a1-\u30fa\u30fc-\u318e\u3192-\u3195\u31a0-\u31ba\u31f0-\u31ff\u3220-\u3229\u3248-\u324f\u3251-\u325f\u3280-\u3289\u32b1-\u32bf\u3400-\u4db5\u4e00-\ua48c\ua4d0-\ua4fd\ua500-\ua60c\ua610-\ua672\ua674-\ua67d\ua67f-\ua6f1\ua717-\ua71f\ua722-\ua788\ua78b-\ua827\ua830-\ua835\ua840-\ua873\ua880-\ua8c4\ua8d0-\ua8f7\ua8fb-\ua92d\ua930-\ua953\ua960-\ua9c0\ua9cf-\ua9d9\uaa00-\uaa59\uaa60-\uaa76\uaa7a-\uaadd\uaae0-\uaaef\uaaf2-\uabea\uabec-\ud7fb\uf900-\ufb28\ufb2a-\ufbb1\ufbd3-\ufd3d\ufd50-\ufdfb\ufe00-\ufe0f\ufe20-\ufe26\ufe70-\ufefc\uff10-\uff19\uff21-\uff3a\uff41-\uff5a\uff66-\uffdc]"
else:
    TOKEN_RANGE = "[0-9A-Za-z\xaa-\xaa\xb2-\xb3\xb5-\xb5\xb9-\xba\xbc-\xbe\xc0-\xd6\xd8-\xf6\xf8-\u02c1\u02c6-\u02d1\u02e0-\u02e4\u02ec-\u02ec\u02ee-\u02ee\u0300-\u0374\u0376-\u037d\u0386-\u0386\u0388-\u03f5\u03f7-\u0481\u0483-\u0559\u0561-\u0587\u0591-\u05bd\u05bf-\u05bf\u05c1-\u05c2\u05c4-\u05c5\u05c7-\u05f2\u0610-\u061a\u0620-\u0669\u066e-\u06d3\u06d5-\u06dc\u06df-\u06e8\u06ea-\u06fc\u06ff-\u06ff\u0710-\u07f5\u07fa-\u082d\u0840-\u085b\u08a0-\u0963\u0966-\u096f\u0971-\u09f1\u09f4-\u09f9\u0a01-\u0aef\u0b01-\u0b6f\u0b71-\u0bf2\u0c01-\u0c7e\u0c82-\u0d75\u0d7a-\u0df3\u0e01-\u0e3a\u0e40-\u0e4e\u0e50-\u0e59\u0e81-\u0f00\u0f18-\u0f19\u0f20-\u0f33\u0f35-\u0f35\u0f37-\u0f37\u0f39-\u0f39\u0f3e-\u0f84\u0f86-\u0fbc\u0fc6-\u0fc6\u1000-\u1049\u1050-\u109d\u10a0-\u10fa\u10fc-\u135f\u1369-\u138f\u13a0-\u13f4\u1401-\u166c\u166f-\u167f\u1681-\u169a\u16a0-\u16ea\u16ee-\u1734\u1740-\u17d3\u17d7-\u17d7\u17dc-\u17f9\u180b-\u180d\u1810-\u193b\u1946-\u19da\u1a00-\u1a1b\u1a20-\u1a99\u1aa7-\u1aa7\u1b00-\u1b59\u1b6b-\u1b73\u1b80-\u1bf3\u1c00-\u1c37\u1c40-\u1c7d\u1cd0-\u1cd2\u1cd4-\u1fbc\u1fbe-\u1fbe\u1fc2-\u1fcc\u1fd0-\u1fdb\u1fe0-\u1fec\u1ff2-\u1ffc\u2070-\u2079\u207f-\u2089\u2090-\u209c\u20d0-\u20f0\u2102-\u2102\u2107-\u2107\u210a-\u2113\u2115-\u2115\u2119-\u211d\u2124-\u2124\u2126-\u2126\u2128-\u2128\u212a-\u212d\u212f-\u2139\u213c-\u213f\u2145-\u2149\u214e-\u214e\u2150-\u2189\u2460-\u249b\u24ea-\u24ff\u2776-\u2793\u2c00-\u2ce4\u2ceb-\u2cf3\u2cfd-\u2cfd\u2d00-\u2d6f\u2d7f-\u2dff\u2e2f-\u2e2f\u3005-\u3007\u3021-\u302f\u3031-\u3035\u3038-\u303c\u3041-\u309a\u309d-\u309f\u30a1-\u30fa\u30fc-\u318e\u3192-\u3195\u31a0-\u31ba\u31f0-\u31ff\u3220-\u3229\u3248-\u324f\u3251-\u325f\u3280-\u3289\u32b1-\u32bf\u3400-\u4db5\u4e00-\ua48c\ua4d0-\ua4fd\ua500-\ua60c\ua610-\ua672\ua674-\ua67d\ua67f-\ua6f1\ua717-\ua71f\ua722-\ua788\ua78b-\ua827\ua830-\ua835\ua840-\ua873\ua880-\ua8c4\ua8d0-\ua8f7\ua8fb-\ua92d\ua930-\ua953\ua960-\ua9c0\ua9cf-\ua9d9\uaa00-\uaa59\uaa60-\uaa76\uaa7a-\uaadd\uaae0-\uaaef\uaaf2-\uabea\uabec-\ud7fb\uf900-\ufb28\ufb2a-\ufbb1\ufbd3-\ufd3d\ufd50-\ufdfb\ufe00-\ufe0f\ufe20-\ufe26\ufe70-\ufefc\uff10-\uff19\uff21-\uff3a\uff41-\uff5a\uff66-\uffdc\U00010000-\U000100fa\U00010107-\U00010133\U00010140-\U00010178\U0001018a-\U0001018a\U000101fd-\U0001039d\U000103a0-\U000103cf\U000103d1-\U00010855\U00010858-\U0001091b\U00010920-\U00010939\U00010980-\U00010a47\U00010a60-\U00010a7e\U00010b00-\U00010b35\U00010b40-\U00011046\U00011052-\U000110ba\U000110d0-\U0001113f\U00011180-\U000111c4\U000111d0-\U00012462\U00013000-\U0001b001\U0001d165-\U0001d169\U0001d16d-\U0001d172\U0001d17b-\U0001d182\U0001d185-\U0001d18b\U0001d1aa-\U0001d1ad\U0001d242-\U0001d244\U0001d360-\U0001d6c0\U0001d6c2-\U0001d6da\U0001d6dc-\U0001d6fa\U0001d6fc-\U0001d714\U0001d716-\U0001d734\U0001d736-\U0001d74e\U0001d750-\U0001d76e\U0001d770-\U0001d788\U0001d78a-\U0001d7a8\U0001d7aa-\U0001d7c2\U0001d7c4-\U0001eebb\U0001f100-\U0001f10a\U00020000-\U0002fa1d\U000e0100-\U000e01ef]"

# A token is a sequence that matches TOKEN_RANGE, or multiple such sequences
# joined only by an apostrophe (as in the word "can't").
TOKEN_RE = re.compile("{0}+(?:'{0}+)*".format(TOKEN_RANGE))


def simple_tokenize(text):
    """
    Split a text into tokens (roughly the same as words).

    >>> simple_tokenize("...testing... 1, 2, 3")
    ['testing', '1', '2', '3']
    >>> simple_tokenize("Apostrophes aren't a problem")
    ['apostrophes', "aren't", 'a', 'problem']
    """
    return [casefold(token) for token in TOKEN_RE.findall(text)]


def untokenize(tokens):
    """
    Combine a list of tokens into a single string of text.
    """
    return ' '.join(tokens)


# This expression scans through a reversed string to find segments of
# camel-cased text. Comments show what these mean, forwards, in preference
# order:
CAMEL_RE = re.compile(r"""
    ^( [A-Z]+                 # A string of all caps, such as an acronym
     | [^A-Z0-9 _]+[A-Z _]    # A single capital letter followed by lowercase
                              #   letters, or lowercase letters on their own
                              #   after a word break
     | [^A-Z0-9 _]*[0-9.]+    # A number, possibly followed by lowercase
                              #   letters
     | [ _]+                  # Extra word breaks (spaces or underscores)
     | [^A-Z0-9]*[^A-Z0-9_ ]+ # Miscellaneous symbols, possibly with lowercase
                              #   letters after them
     )
""", re.VERBOSE)


def un_camel_case(text):
    r"""
    Splits apart words that are written in CamelCase.

    Bugs:

    - Non-ASCII characters are treated as lowercase letters, even if they are
      actually capital letters.

    Examples:

    >>> un_camel_case('1984ZXSpectrumGames')
    '1984 ZX Spectrum Games'

    >>> un_camel_case('aaAa aaAaA 0aA  AAAa!AAA')
    'aa Aa aa Aa A 0a A AA Aa! AAA'

    >>> un_camel_case('MotörHead')
    'Mot\xf6r Head'

    >>> un_camel_case('MSWindows3.11ForWorkgroups')
    'MS Windows 3.11 For Workgroups'

    This should not significantly affect text that is not camel-cased:

    >>> un_camel_case('ACM_Computing_Classification_System')
    'ACM Computing Classification System'

    >>> un_camel_case('Anne_Blunt,_15th_Baroness_Wentworth')
    'Anne Blunt, 15th Baroness Wentworth'

    >>> un_camel_case('Hindi-Urdu')
    'Hindi-Urdu'
    """
    revtext = text[::-1]
    pieces = []
    while revtext:
        match = CAMEL_RE.match(revtext)
        if match:
            pieces.append(match.group(1))
            revtext = revtext[match.end():]
        else:
            pieces.append(revtext)
            revtext = ''
    revstr = ' '.join(piece.strip(' _') for piece in pieces
                      if piece.strip(' _'))
    return revstr[::-1].replace('- ', '-')
