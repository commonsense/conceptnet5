#!/bin/bash -e
dbname=${CONCEPTNET_DB_NAME:-conceptnet5}

check_disk_space() {
    kb_free=$(df -Pk data | awk '/[0-9]%/{print $(NF-2)}')
    if [ $kb_free -lt 200000000 ]; then
        echo "To build ConceptNet, you will need at least 200 GB of disk space"
        echo "available for the ./data directory. Try making it a symbolic link"
        echo "to a larger drive."
        echo
        echo "Your data directory is currently on this drive:"
        df -h data
        exit 1
    fi
}

complain_db () {
    echo
    echo "You don't have access to the '$dbname' PostgreSQL database."
    echo "You may need to install PostgreSQL 9.5 or later, create this database,"
    echo "give yourself access to it, or set \$CONCEPTNET_DB_NAME to a database"
    echo "that you can use."
    exit 1
}

check_db () {
    cn5-db check || complain_db
}

check_disk_space
pip install -e '.[vectors]'
check_db
snakemake --resources 'ram=24' -j
