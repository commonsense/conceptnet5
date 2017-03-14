#!/bin/bash
# After building ConceptNet, this script uploads the built PostgreSQL data
# that the data-loader will use.
if [ $# -eq 0 ]; then
  echo "Usage: ./upload.sh VERSION"
  exit 1
fi

aws s3 cp --recursive data/psql s3://conceptnet/precomputed-data/2016/psql/$1/ --exclude *.csv --exclude *done --acl public-read
