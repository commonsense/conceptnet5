#!/bin/sh
source secrets.sh
export MONGO_HOST=67.202.1.34
mongoimport --upsert --upsertFields uri -h $MONGO_HOST -u $USERNAME -p $PASSWORD -d conceptnet -c nodes $1.nodes.json
mongoimport --upsert --upsertFields key -h $MONGO_HOST -u $USERNAME -p $PASSWORD -d conceptnet -c edges $1.edges.json
#mongoimport -h $MONGO_HOST -d conceptnet -c scoredEdges $1.scored.json
