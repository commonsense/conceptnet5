#!/bin/sh
docker-compose down &&\
    docker volume rm -f conceptnet5_psql &&\
    docker volume rm -f conceptnet5_cn5data &&\
    docker volume rm -f conceptnet5_nginx &&\
    docker-compose up --build
