from __future__ import print_function, unicode_literals
import json
import sys
import codecs

# Python 2/3 compatibility
if sys.version_info.major >= 3:
    string_type = str
    from io import StringIO
else:
    string_type = basestring
    from StringIO import StringIO


class JSONStreamWriter(object):
    """
    Write a stream of data in "JSON stream" format. This format contains a
    number of JSON objects, separated by line breaks. Line breaks are not
    allowed within a JSON object, which is stricter than the JSON standard.

    The suggested extension for this format is '.jsons'.

    The stream can be specified with a filename, or it can be an existing
    stream such as `sys.stdout`. As a special case, it will not close
    `sys.stdout` even if it's asked to, because that is usually undesired
    and causes things to crash.
    """
    def __init__(self, filename_or_stream):
        if hasattr(filename_or_stream, 'write'):
            self.stream = filename_or_stream
        else:
            self.stream = codecs.open(filename_or_stream, 'w', encoding='utf-8')

    def write(self, obj):
        if isinstance(obj, string_type):
            raise ValueError(
                "%r is already a string. It shouldn't be written to a JSON stream."
                % obj
            )

        line = json.dumps(obj, ensure_ascii=False)
        print(line, file=self.stream)

    def close(self):
        if self.stream is not sys.stdout:
            self.stream.close()


def read_json_stream(filename_or_stream):
    """
    Read a stream of data in "JSON stream" format. Returns a generator of the
    decoded objects.
    """
    if hasattr(filename_or_stream, 'read'):
        stream = filename_or_stream
    else:
        stream = codecs.open(filename_or_stream, encoding='utf-8')
    for line in stream:
        line = line.strip()
        if line:
            yield json.loads(line)

