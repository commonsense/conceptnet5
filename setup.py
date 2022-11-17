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
        'snakemake == 5.5.4', 'click == 8.0.3', 'requests == 2.26.0', 'ftfy == 6.0.3', 'msgpack-python == 0.5.6', 'numpy == 1.21.4',
        'langcodes == 3.3.0', 'wordfreq == 2.5.1',
        'xmltodict == 0.11.0', 'ordered_set == 4.0.2', 'psycopg2-binary == 2.9.2',
        'marisa-trie == 0.7.7', 'tables == 3.6.1'
    ],
    python_requires='>=3.5',
    tests_require=['pytest', 'PyLD'],
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
        'vectors': ['numpy == 1.21.4', 'scipy == 1.9.1', 'statsmodels == 0.13.1', 'tables == 3.6.1', 'pandas == 1.3.5', 'scikit-learn == 1.0.1',
                    'mecab-python3 == 1.0.4', 'jieba == 0.42.1', 'marisa_trie == 0.7.7', 'matplotlib == 3.5.1', 'annoy == 1.17.1']
    },
)
