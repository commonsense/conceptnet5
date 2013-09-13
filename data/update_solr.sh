#!/bin/bash
die () {
    echo >&2 "$@"
    exit 1
}

[ "$#" -eq 1 ] || die "Usage: update_solr.sh hostname"

echo "Clearing old data"
curl "http://$1:8983/solr/update?commit=true" -H 'Content-type: text/xml' --data-binary '<delete><query>*:*</query></delete>'
for solr_file in solr/*.json
do
    echo "Importing $solr_file"
    curl "http://$1:8983/solr/update/json?commit=true" -H 'Content-type: application/json' --data-binary @$solr_file
done

