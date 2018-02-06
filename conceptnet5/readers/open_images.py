import gzip
import re

import regex

from conceptnet5.edges import make_edge
from conceptnet5.formats.msgpack_stream import MsgpackStreamWriter
from conceptnet5.nodes import standardized_concept_uri
from conceptnet5.uri import Licenses

DATASET = '/d/open_images'
LICENSE = Licenses.cc_attribution
SOURCE = [{'contributor': '/s/resource/open_images/2017_11'}]


def handle_file(input, output):
    pass
