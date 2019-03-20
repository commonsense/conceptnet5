#!/bin/bash

export CONCEPTNET_BUILD_TEST=1
export CONCEPTNET_BUILD_DATA=testdata
export CONCEPTNET_DB_NAME=conceptnet-test
nosetests --with-doctest conceptnet5 && nosetests && nosetests tests/small-build && echo "Success."
