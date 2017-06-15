#!/bin/bash

export CONCEPTNET_BUILD_TEST=1
export CONCEPTNET_BUILD_DATA=testdata
dropdb conceptnet-test 2>/dev/null || true
createdb conceptnet-test
build_test () {
    snakemake -q clean &&\
    snakemake -j 4 test &&\
    confirm_diff || complain_diff
}

confirm_diff () {
    diff -ur -x '*.msgpack' testdata/reference/edges testdata/edges &&\
    diff -ur -x '*.msgpack' testdata/reference/assertions testdata/assertions &&\
    diff -ur -x '*.msgpack' testdata/reference/assoc testdata/assoc
}

complain_diff () {
    echo
    echo "The files built in ./testdata didn't match the desired output in ./testdata/reference."
    echo "Look at the diff above to see what didn't match."
    exit 1
}

nosetests --with-doctest conceptnet5 && build_test && nosetests && nosetests tests/small-build && echo "Success."
