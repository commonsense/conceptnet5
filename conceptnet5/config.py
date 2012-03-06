"""
Contains configuration for accessing the database.
"""
import os
import json
from getpass import getpass

LANGUAGES = {
    'English': 'en',
    
    'Afrikaans': 'af',
    'Arabic': 'ar',
    'Armenian': 'hy',
    'Basque': 'eu',
    'Belarusian': 'be',
    'Bengali': 'bn',
    'Bosnian': 'bs',
    'Bulgarian': 'bg',
    'Burmese': 'my',
    'Chinese': 'zh',
    'Crimean Tatar': 'crh',
    'Croatian': 'hr',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'Esperanto': 'eo',
    'Estonian': 'et',
    'Finnish': 'fi',
    'French': 'fr',
    'Galician': 'gl',
    'German': 'de',
    'Greek': 'el',
    'Hebrew': 'he',
    'Hindi': 'hi',
    'Hungarian': 'hu',
    'Icelandic': 'is',
    'Ido': 'io',
    'Indonesian': 'id',
    'Irish': 'ga',
    'Italian': 'it',
    'Japanese': 'ja',
    'Kannada': 'kn',
    'Kazakh': 'kk',
    'Khmer': 'km',
    'Korean': 'ko',
    'Kyrgyz': 'ky',
    'Lao': 'lo',
    'Latin': 'la',
    'Lithuanian': 'lt',
    'Lojban': 'jbo',
    'Macedonian': 'mk',
    'Min Nan': 'nan',
    'Malagasy': 'mg',
    'Mandarin': 'zh',
    'Norwegian': 'no',
    'Pashto': 'ps',
    'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Romanian': 'ro',
    'Russian': 'ru',
    'Sanskrit': 'sa',
    'Sinhalese': 'si',
    'Scots': 'sco',
    'Scottish Gaelic': 'gd',
    'Serbian': 'sr',
    'Slovak': 'sk',
    'Slovene': 'sl',
    'Slovenian': 'sl',
    'Spanish': 'es',
    'Swahili': 'sw',
    'Swedish': 'sv',
    'Tajik': 'tg',
    'Tamil': 'ta',
    'Thai': 'th',
    'Turkish': 'tr',
    'Turkmen': 'tk',
    'Ukrainian': 'uk',
    'Urdu': 'ur',
    'Uzbek': 'uz',
    'Vietnamese': 'vi',
    u'英語': 'en',
    u'日本語': 'ja'
}

def _mkdir(newdir):
    """
    http://code.activestate.com/recipes/82465/
    
    works the way a good mkdir should :)

        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("A file with the same name as the desired " \
                      "directory, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)
        if tail:
            os.mkdir(newdir)

def get_config_dir():
    if os.name == 'nt':
        return os.path.expanduser('~/conceptnet')
    else:
        return os.path.expanduser('~/.conceptnet')

def get_auth_filename():
    return os.path.join(get_config_dir(), 'conceptnet5.auth.json')

def get_auth():
    try:
        from conceptnet5 import secrets
        return {'username': secrets.USERNAME,
                'password': secrets.PASSWORD}
    except ImportError:
        filename = get_auth_filename()
        if not os.access(filename, os.F_OK):
            make_auth()
        return json.load(open(get_auth_filename()))

def make_auth():
    dir = get_config_dir()
    _mkdir(dir)
    outfn = get_auth_filename()
    
    print "You need to provide the username and password for accessing the DB."
    print "This will be saved as:", outfn
    username = raw_input("Username: ")
    password = getpass("Password: ")
    
    out = open(outfn, 'w')
    json.dump({'username': username, 'password': password}, out, indent=2)
    out.close()
    os.chmod(outfn, 0600)

