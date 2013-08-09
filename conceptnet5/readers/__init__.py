import sys


def transform_stream(func, stream_in=None, stream_out=None):
    if stream_in is None:
        stream_in = sys.stdin
    if stream_out is None:
        stream_out = sys.stdout
    for line in sys.stdin:
        line = line.strip().decode('utf-8')
        for result in func(line):
            print >> stream_out, result.encode('utf-8')

