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
    install_requires=['nltk >= 3.0b2', 'assoc-space', 'xmltodict', 'pyyaml', 'flask', 'flask-cors', 'grako > 3', 'ftfy', 'msgpack-python'],
    license = 'GPLv3'
)

