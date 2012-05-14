import site
import os
os.environ['LUMINOSO_DATA'] = '/srv/conceptnet5.1/lumi_data'
site.addsitedir('/srv/conceptnet5.1/env/lib/python2.6/site-packages')
from conceptnet5.api import app as application
