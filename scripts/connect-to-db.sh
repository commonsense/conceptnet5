#!/bin/sh
docker exec -it conceptnet5_db_1 su postgres -c 'psql conceptnet5'
