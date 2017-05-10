#!/usr/bin/env python
from setuptools import setup, find_packages, Command
from setuptools.command.install import install
from setuptools.command.develop import develop
import sys

packages = find_packages()
version_str = '0.1'

if sys.version_info.major < 3:
    print("The ConceptNet 5 code can only run in Python 3.")
    sys.exit(1)


setup(
    name = 'conceptnet-viz',
    version = version_str,
    description = 'Produces an explorable SVG visualization of ConceptNet',
    author = "Rob Speer",
    author_email = 'rob@luminoso.com',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'conceptnet >= 5.5.4',
        'freetype-py',
        'Python-fontconfig',
        'svgwrite',
        'colormath'
    ],
    license = 'Apache License 2.0',
)
