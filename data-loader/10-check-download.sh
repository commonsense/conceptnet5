#!/bin/sh

PRECOMPUTED_PSQL_URL=http://conceptnet.s3.amazonaws.com/precomputed-data/2016/psql/5.5.5
PRECOMPUTED_VECTOR_URL=http://conceptnet.s3.amazonaws.com/precomputed-data/2016/numberbatch/17.05
DATA=/data/conceptnet
NAMES='edges edge_sources edge_features nodes node_prefixes sources relations'

get_db_files() {
    for name in $NAMES; do
        curl $PRECOMPUTED_PSQL_URL/$name.csv.gz > $DATA/psql/$name.csv.gz
    done
    sha256sum $DATA/psql/*.csv.gz > $DATA/local/sha256sums.computed.txt
    diff $DATA/local/sha256sums.txt $DATA/local/sha256sums.computed.txt || panic
}

panic() {
    rm $DATA/psql/*.csv.gz
    echo "SHA-256 hashes of input files don't match. The database will not be built."
    echo "This could indicate a failed download, a version mismatch, or your HTTP connection getting hijacked."
    exit 1
}

mkdir -p $DATA/psql
mkdir -p $DATA/vectors

# Get semantic vectors (ConceptNet Numberbatch Mini) that would be
# computationally expensive to compute
if [ ! -e $DATA/vectors/mini.h5 ]; then
    curl $PRECOMPUTED_VECTOR_URL/mini.h5 > $DATA/vectors/mini.h5
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
