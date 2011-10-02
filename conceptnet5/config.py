"""
Contains configuration for accessing the database.
"""
import os
import json
from getpass import getpass

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

