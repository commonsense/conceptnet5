#!/bin/sh
export MONGO_HOST=67.202.46.13
mongoimport --upsert --upsertFields uri -h $MONGO_HOST -d conceptnet -c nodes $1.nodes.json
mongoimport --upsert --upsertFields key -h $MONGO_HOST -d conceptnet -c edges $1.edges.json
