#!/usr/bin/env python
from setuptools import setup, find_packages, Command
from setuptools.command.install import install
from setuptools.command.develop import develop
import sys

packages = find_packages()
version_str = '5.5.5'

if sys.version_info.major < 3:
    print("The ConceptNet 5 code can only run in Python 3.")
    sys.exit(1)


setup(
    name = 'conceptnet-web',
    version = version_str,
    description = 'Runs the Web site and API for ConceptNet',
    author = "Rob Speer",
    author_email = 'rob@luminoso.com',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'conceptnet >= %s' % version_str,
        'limits', 'flask==0.11', 'flask-cors', 'flask-limiter',
        'langcodes >= 1.3', 'jinja2-highlight', 'pygments', 'raven[flask]'
    ],
    license = 'Apache License 2.0',
)
