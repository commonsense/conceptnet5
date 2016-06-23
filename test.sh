#!/bin/bash

export CONCEPTNET_BUILD_TEST=1
build_test () {
    snakemake -q clean
    snakemake -j 4 test
    diff -ur -x '*.msgpack' testdata/reference/edges testdata/edges
    diff -ur -x '*.msgpack' testdata/reference/assertions testdata/assertions
    diff -ur -x '*.msgpack' testdata/reference/external testdata/external
    diff -ur -x '*.msgpack' testdata/reference/assoc testdata/assoc
}

nosetests --with-doctest conceptnet5 && build_test && nosetests && echo "Success."
