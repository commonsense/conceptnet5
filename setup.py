#!/usr/bin/env python
import sys

from setuptools import Command, find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install

packages = find_packages()
version_str = '5.7.0'

if sys.version_info.major < 3:
    print("The ConceptNet 5 code can only run in Python 3.")
    sys.exit(1)


DESCRIPTION = open('README.md').read()


setup(
    name='ConceptNet',
    version=version_str,
    description='A semantic network of general knowledge',
    long_description=DESCRIPTION,
    long_description_content_type='text/markdown',
    author="Robyn Speer",
    author_email='rspeer@luminoso.com',
    packages=packages,
    include_package_data=True,
    exclude_package_data={'conceptnet5': ['support_data/testdata']},
    install_requires=[
        'snakemake', 'click', 'requests', 'ftfy', 'msgpack-python', 'numpy',
        'langcodes >= 1.4.1', 'wordfreq >= 2.0.1',
        'xmltodict >= 0.11.0, < 0.12.0', 'ordered_set', 'psycopg2-binary',
        'marisa-trie'
    ],
    python_requires='>=3.5',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'cn5-vectors = conceptnet5.vectors.cli:cli',
            'cn5-read = conceptnet5.readers.cli:cli',
            'cn5-build = conceptnet5.builders.cli:cli',
            'cn5-convert = conceptnet5.formats.convert:cli',
            'cn5-db = conceptnet5.db.cli:cli'
        ]
    },
    extras_require={
        'vectors': ['numpy', 'scipy', 'statsmodels', 'tables', 'pandas', 'scikit-learn',
                    'mecab-python3', 'jieba', 'marisa_trie', 'matplotlib >= 2', 'annoy']
    },
)
