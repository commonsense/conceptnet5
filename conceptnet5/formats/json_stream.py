from __future__ import print_function, unicode_literals
import json
import sys
import codecs

# Python 2/3 compatibility
if sys.version_info.major >= 3:
    string_type = str
    def opener(filename):
        return open(filename, encoding='utf-8', newline='\n')
else:
    string_type = basestring
    def opener(filename):
        return codecs.open(filename, encoding='utf-8')


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

    On Python 2, this will glitch out when trying to read JSON objects
    containing Unicode characters U+2018 or U+2019. This is because the
    "codecs" module, the only thing that reads Unicode input streams on Python
    2, considers them to be line breaks, and can't be convinced otherwise.

    We could be fully compatible with Python 2 if we read the input as bytes
    and then decode it, but then we wouldn't be able to pass in Unicode
    streams at all, which is a big loss. 

    So, keep in mind that this function can give different results on Python 2
    and 3. When building ConceptNet, the Python 3 version is correct.
    """
    errors = 0
    if hasattr(filename_or_stream, 'read'):
        stream = filename_or_stream
    else:
        stream = opener(filename_or_stream)
    for line in stream:
        line = line.strip()
        if line:
            try:
                yield json.loads(line)
            except ValueError:
                print("Malformed JSON: %r" % line)
                errors += 1
                if errors >= 5:
                    print("Re-raising because too many JSON errors have occurred.")
                    raise

