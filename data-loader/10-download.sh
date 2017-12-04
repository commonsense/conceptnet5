#!/bin/sh

PRECOMPUTED_PSQL_URL=http://conceptnet.s3.amazonaws.com/precomputed-data/2016/psql/5.5.5
PRECOMPUTED_VECTOR_URL=http://conceptnet.s3.amazonaws.com/precomputed-data/2016/numberbatch/17.06
DATA=/data/conceptnet
CHECKSUM=/checksum
NAMES='edges edge_sources edge_features nodes node_prefixes sources relations'

get_db_files() {
    for name in $NAMES; do
        wget -nv -O $DATA/psql/$name.csv.gz $PRECOMPUTED_PSQL_URL/$name.csv.gz
    done
}

mkdir -p $DATA/psql
mkdir -p $DATA/vectors

# Get semantic vectors (ConceptNet Numberbatch Mini) that would be
# computationally expensive to compute
if [ ! -e $DATA/vectors/mini.h5 ]; then
    wget -nv -O $DATA/vectors/mini.h5 $PRECOMPUTED_VECTOR_URL/mini.h5
fi
# Get the database input files
if [ ! -e $DATA/psql/edges.csv.gz ]; then
    get_db_files
fi

for name in $NAMES; do
    echo "Extracting $name"
    gunzip -c $DATA/psql/$name.csv.gz > $DATA/psql/$name.csv
    chown postgres.postgres $DATA/psql/$name.csv
done

touch "$DATA/psql/done"
