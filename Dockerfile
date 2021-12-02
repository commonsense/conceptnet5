#Download base image ubuntu 20.04
FROM ubuntu:20.04

LABEL maintainer="mmachado@ibm.com"

LABEL description="This is custom Docker Image for Conceptnet 5."

#RUN apt-get install postgresql-10 -y

ARG DEBIAN_FRONTEND=noninteractive
ARG CONCEPTNET_DB_NAME=conceptnet5
ARG CONCEPTNET_DB_USER=postgres
ARG CONCEPTNET_DB_HOSTNAME=127.0.0.1	
ARG CONCEPTNET_DB_PASSWORD
ARG CONCEPTNET_DB_PORT=5432


#Define the ENV variable
ENV CONCEPTNET_DATA=/conceptnet_data

ENV CONCEPTNET_DB_PASSWORD=$CONCEPTNET_DB_PASSWORD
ENV CONCEPTNET_DB_HOSTNAME=$CONCEPTNET_DB_HOSTNAME
ENV CONCEPTNET_DB_NAME=$CONCEPTNET_DB_NAME
ENV CONCEPTNET_DB_USER=$CONCEPTNET_DB_USER

RUN apt-get update
RUN apt-get install -y build-essential python3-pip python3-dev libhdf5-dev libmecab-dev mecab-ipadic-utf8 
# RUN postgresql postgresql-contrib

RUN mkdir data

# RUN PGPASSWORD=$CONCEPTNET_DB_PASSWORD psql -U $CONCEPTNET_DB_USER
# RUN CREATE DATABASE $CONCEPTNET_DB_NAME;
# RUN \q

COPY . /usr/src
WORKDIR /usr/src

RUN pip install -U pip
RUN pip install -e .
RUN pip install -e '.[vectors]'

RUN ./build.sh

RUN pip install -e web

RUN chown -R 1001:0 /usr/src
USER 1001

WORKDIR /usr/src/web
CMD ["python3", "conceptnet_web/api.py"]