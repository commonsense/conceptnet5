#!/bin/bash

export CONCEPTNET_BUILD_TEST=0

nosetests -v tests/full-build && echo "Success."
