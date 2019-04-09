import logging
import os

from raven.contrib.flask import Sentry

from conceptnet5.util import get_data_filename


def try_configuring_sentry(app):
    dsn_path = get_data_filename('deploy/sentry-dsn.txt')
    if os.path.exists(dsn_path):
        dsn = open(dsn_path).read().strip()
        return Sentry(app, logging=True, level=logging.ERROR, dsn=dsn)
    else:
        print("Sentry is not configured.")
        return None
