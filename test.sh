#!/bin/bash

export CONCEPTNET_BUILD_TEST=1
build_test () {
    snakemake -q clean
    snakemake -j 4 test
    diff -ur -x '*.msgpack' testdata/edges testdata/reference/edges
    diff -ur -x '*.msgpack' testdata/assertions testdata/reference/assertions
    diff -ur -x '*.msgpack' testdata/external testdata/reference/external
    diff -ur -x '*.msgpack' testdata/assoc testdata/reference/assoc
}

nosetests --with-doctest conceptnet5 && build_test && nosetests && echo "Success."
