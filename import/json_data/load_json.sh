#!/bin/sh
#source secrets.sh
export MONGO_HOST=ganymede.csc.media.mit.edu:30000
mongoimport --upsert --upsertFields uri -h $MONGO_HOST -d conceptnet -c nodes $1.nodes.json
mongoimport --upsert --upsertFields key -h $MONGO_HOST -d conceptnet -c edges $1.edges.json
