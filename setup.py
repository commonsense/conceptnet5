#!/usr/bin/env python
from setuptools import setup, find_packages, Command
from setuptools.command.install import install
from setuptools.command.develop import develop
import sys

packages = find_packages()
version_str = '5.5.2'

if sys.version_info.major < 3:
    print("The ConceptNet 5 code can only run in Python 3.")
    sys.exit(1)


setup(
    name = 'ConceptNet',
    version = version_str,
    description = 'A semantic network of general knowledge',
    author = "Rob Speer",
    author_email = 'conceptnet@media.mit.edu',
    packages=packages,
    include_package_data=True,
    exclude_package_data={'conceptnet5': ['support_data/testdata']},
    install_requires=[
        'snakemake', 'click', 'requests', 'ftfy', 'numpy', 'scipy',
        'msgpack-python', 'langcodes >= 1.3', 'wordfreq >= 1.5',
        'xmltodict', 'ordered_set', 'pg8000'
    ],
    license = 'Apache License 2.0',
    entry_points = {
        'console_scripts': [
            'cn5-vectors = conceptnet5.vectors.cli:cli',
            'cn5-read = conceptnet5.readers.cli:cli',
            'cn5-convert = conceptnet5.formats.convert:cli',
            'cn5-db = conceptnet5.db.cli:cli'
        ]
    },
    extras_require={
        'vectors': ['numpy', 'scipy', 'statsmodels', 'tables', 'pandas', 'scikit-learn']
    },
)
