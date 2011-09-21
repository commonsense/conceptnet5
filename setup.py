#!/usr/bin/env python
from setuptools import setup, find_packages

packages = find_packages()
version_str = '5.0a1'

setup(
    name = 'ConceptNet5',
    version = version_str,
    description = 'A semantic network of general knowledge',
    author = "Rob Speer, Commonsense Computing Group',
    author_email = 'conceptnet@media.mit.edu',
    packages=packages,
    install_requires=['csc-utils >= 0.6', 'neo4j-rest-client'],
    license = 'GPLv3'
)

