#!/bin/sh
mongoimport --upsert --upsertFields uri -h tortoise.csc.media.mit.edu -d conceptnet -c nodes $0.nodes.json
mongoimport --upsert --upsertFields key -h tortoise.csc.media.mit.edu -d conceptnet -c edges $0.edges.json
