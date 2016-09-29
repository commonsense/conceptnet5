#!/bin/bash
docker-compose build conceptnet && \
docker-compose run conceptnet scripts/build.sh
