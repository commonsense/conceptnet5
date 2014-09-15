#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

packages = find_packages()
version_str = '5.3b1'

setup(
    name = 'ConceptNet',
    version = version_str,
    description = 'A semantic network of general knowledge',
    author = "Rob Speer",
    author_email = 'conceptnet@media.mit.edu',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'nltk >= 3.0b1', 'xmltodict', 'pyyaml',
        'flask', 'flask-cors', 'flask-limiter', 'grako > 3', 'ftfy',
        'msgpack-python'
    ],
    # assoc-space >= 1.0b1 is required for using assoc-space features, but it's
    # not required for all of ConceptNet
    license = 'GPLv3'
)

