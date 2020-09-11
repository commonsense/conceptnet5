#!/bin/bash
# Upload big files to Zenodo.
# Script adapted from https://github.com/jhpoelen/zenodo-upload
#
# usage: ./zenodo_upload.sh [filename]
#

set -xe

DEPOSITION=$1
FILEPATH=$2
FILENAME=$(basename $FILEPATH)

BUCKET=$(curl -H "Accept: application/json" -H "Authorization: Bearer $ZENODO_TOKEN" "https://www.zenodo.org/api/deposit/depositions/$DEPOSITION" | jq --raw-output .links.bucket)


curl --progress-bar --upload-file $FILEPATH $BUCKET/$FILENAME?access_token=$ZENODO_TOKEN
echo
