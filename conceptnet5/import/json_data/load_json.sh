#!/bin/sh
export MONGO_HOST=ec2-75-101-189-5.compute-1.amazonaws.com
mongoimport --upsert --upsertFields uri -h $MONGO_HOST -d conceptnet -c nodes $1.nodes.json
mongoimport --upsert --upsertFields key -h $MONGO_HOST -d conceptnet -c edges $1.edges.json
