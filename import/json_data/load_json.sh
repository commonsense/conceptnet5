#!/bin/sh
source secrets.sh
export MONGO_HOST=50.17.55.143
mongoimport --upsert --upsertFields uri -h $MONGO_HOST -d conceptnet -c nodes $1.nodes.json
mongoimport --upsert --upsertFields key -h $MONGO_HOST -d conceptnet -c edges $1.edges.json
#mongoimport -h $MONGO_HOST -d conceptnet -c scoredEdges $1.scored.json
