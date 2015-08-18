#!/bin/bash
# After building ConceptNet, this script uploads the built data in the data/dist/
# directory to the ConceptNet server.
if [ $# -eq 0 ]; then
  echo "Usage: ./upload.sh DATE"
  exit 1
fi

rsync -Pavz data/dist/$1 conceptnet5.media.mit.edu:/data/downloads
