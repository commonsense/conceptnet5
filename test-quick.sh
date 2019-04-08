#!/bin/bash
#
# If you've just run ./test.sh and you want to run it again with the same data,
# this command will run the tests that depend on the test data without
# rebuilding it.

export CONCEPTNET_BUILD_TEST=1
export CONCEPTNET_BUILD_DATA=testdata
export CONCEPTNET_DB_NAME=conceptnet-test
nosetests --with-doctest conceptnet5 && nosetests && nosetests -v tests/small-build $@ && echo "Success."
