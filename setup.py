#!/usr/bin/env python
from setuptools import setup, find_packages
import sys

packages = find_packages()
version_str = '5.2.3'

if sys.version_info.major == 2:
    nltk_version = 'nltk'
else:
    nltk_version = 'nltk >= 3.0a'

setup(
    name = 'ConceptNet',
    version = version_str,
    description = 'A semantic network of general knowledge',
    author = "Rob Speer",
    author_email = 'conceptnet@media.mit.edu',
    packages=packages,
    install_requires=[nltk_version, 'assoc-space', 'xmltodict', 'pyyaml', 'flask', 'ftfy'],
    license = 'GPLv3'
)

