#!/usr/bin/env python
import sys

from setuptools import Command, find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install

packages = find_packages()
version_str = '5.8.1'

if sys.version_info.major < 3:
    print("The ConceptNet 5 code can only run in Python 3.")
    sys.exit(1)


setup(
    name = 'conceptnet-web',
    version = version_str,
    description = 'Runs the Web site and API for ConceptNet',
    author = "Robyn Speer",
    author_email = 'rspeer@luminoso.com',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'conceptnet >= %s' % version_str,
        'limits == 2.3', 'flask == 2.0.2', 'flask-cors == 3.0.10', 'flask-limiter == 2.7.0',
        'langcodes == 3.3.0', 'jinja2-highlight == 0.6.1', 'pygments == 2.10.0', 'raven[flask] == 6.10.0'
    ],
    license = 'Apache License 2.0',
)
