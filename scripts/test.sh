#!/bin/bash

export CONCEPTNET_BUILD_TEST=1
dropdb conceptnet-test 2>/dev/null || true
createdb conceptnet-test
build_test () {
    snakemake -q clean &&\
    snakemake -j 4 test &&\
    diff -ur -x '*.msgpack' testdata/reference/edges testdata/edges &&\
    diff -ur -x '*.msgpack' testdata/reference/assertions testdata/assertions &&\
    diff -ur -x '*.msgpack' testdata/reference/assoc testdata/assoc
}

nosetests --with-doctest conceptnet5 && build_test && nosetests && nosetests tests/post-build && echo "Success."
