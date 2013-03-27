#!/bin/sh
#
# Usage: ./import-solr-json.sh <files to import>
# Example: ./import-solr-json.sh conceptnet5*-solr-json/* 

for i in $@; do
  echo Importing $i
  curl 'http://salmon.media.mit.edu:8983/solr/update/json?commit=true' --data-binary @$i -H 'Content-type:application/json'
done
