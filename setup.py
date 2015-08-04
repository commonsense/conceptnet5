#!/usr/bin/env python
from setuptools import setup, find_packages, Command
from setuptools.command.install import install
from setuptools.command.develop import develop
import sys

packages = find_packages()
version_str = '5.4.0'

if sys.version_info.major < 3:
    langcodes_req = 'langcodes-py2 == 1.1.1'
else:
    langcodes_req = 'langcodes == 1.1.1'


class NLTKDownloadCommand(Command):
    """
    Get the boilerplate out of the way for commands that take no options.
    """
    description = "Download necessary data to use with NLTK"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from conceptnet5.language import nltk_download
        nltk_download()


setup(
    name = 'ConceptNet',
    version = version_str,
    description = 'A semantic network of general knowledge',
    author = "Rob Speer",
    author_email = 'conceptnet@media.mit.edu',
    packages=packages,
    include_package_data=True,
    install_requires=[
        'nltk >= 3.0b1', 'xmltodict', 'pyyaml', 'requests',
        'flask', 'flask-cors', 'flask-limiter', 'grako > 3', 'ftfy',
        'msgpack-python', langcodes_req
    ],
    # assoc-space >= 1.0b1 is required for using assoc-space features, but it's
    # not required for all of ConceptNet
    license = 'GPLv3',
    cmdclass = {
        'nltk_download': NLTKDownloadCommand,
    }
)
