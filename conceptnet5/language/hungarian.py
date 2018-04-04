import unicodedata
import re


PRÓSZÉKY_ACCENTS = {
    '1': '\N{COMBINING ACUTE ACCENT}',
    '2': '\N{COMBINING DIAERESIS}',
    '3': '\N{COMBINING DOUBLE ACUTE ACCENT}',
}

PRÓSZÉKY_PL_EXCEPTIONS = {
    # These are ambiguous with the Hungarian á and é; we'll fix it later
    # 'A1': 'Ą',
    # 'a1': 'ą',
    'L1': 'Ł',
    'l1': 'ł',
    'Z2': 'Ż',
    'z2': 'ż'
}

ACCENTED_LETTER_RE = re.compile(r'([ACEILNOSUYZaceilnosuyz])([123])')


def _decode_accent(match):
    letter = match.group(1)
    digit = match.group(2)
    combo = letter + digit
    if combo in PRÓSZÉKY_PL_EXCEPTIONS:
        return PRÓSZÉKY_PL_EXCEPTIONS[combo]
    else:
        accent = PRÓSZÉKY_ACCENTS[digit]
        return unicodedata.normalize('NFC', letter + accent)


def decode_prószéky(text, lang='hu'):
    """
    Converts text from the Prószéky encoding, an ASCII encoding of Hungarian
    where the digits 1, 2, and 3 represent three types of accents.

    In the 4lang project, this encoding is additionally used for Polish, so
    this function has to be prepared to produce accented letters that are not
    in the Hungarian alphabet.

    Accents on the vowels 'a' and 'e' have to be handled differently in
    Hungarian and Polish. In Hungarian, "a1" and "e1" are "á" and "é", while
    in Polish, they are "ą" and "ę". The 'lang' parameter to this function
    determines which accented vowels are output.

    In the spirit of embracing Unicode and avoiding silly ambiguous ways to
    smash things into ASCII in the future, this function name is in proper
    Unicode.

    >>> decode_prószéky("evo3eszko2z")
    'evőeszköz'
    >>> decode_prószéky("styczen1")
    'styczeń'
    >>> decode_prószéky("sza1z", 'hu')
    'száz'
    >>> decode_prószéky("ogla1daja1c", 'pl')
    'oglądając'
    """
    result = ACCENTED_LETTER_RE.sub(_decode_accent, text)
    if lang == 'pl':
        result = result.replace('Á', 'Ą').replace('á', 'ą').replace('É', 'Ę').replace('é', 'ę')
    return result
