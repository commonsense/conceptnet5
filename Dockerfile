#Download base image ubuntu 20.04
FROM ubuntu:20.04

LABEL maintainer="mmachado@ibm.com"

LABEL description="This is custom Docker Image for Conceptnet 5."

#RUN apt-get install postgresql-10 -y

ARG DEBIAN_FRONTEND=noninteractive
ARG CONCEPTNET_DB_NAME=conceptnet5
ARG CONCEPTNET_DB_USER=postgres
ARG CONCEPTNET_DB_HOSTNAME=localhost	
ARG CONCEPTNET_DB_PASSWORD
ARG CONCEPTNET_DB_PORT=5432


#Define the ENV variable
ENV CONCEPTNET_DB_PASSWORD=$CONCEPTNET_DB_PASSWORD
ENV CONCEPTNET_DB_HOSTNAME=$CONCEPTNET_DB_HOSTNAME
ENV CONCEPTNET_DB_NAME=$CONCEPTNET_DB_NAME
ENV CONCEPTNET_DB_USER=$CONCEPTNET_DB_USER
ENV POSTGRES_DB=$CONCEPTNET_DB_NAME
ENV POSTGRES_USER=$CONCEPTNET_DB_USER
ENV POSTGRES_PASSWORD=$CONCEPTNET_DB_PASSWORD

RUN apt-get update
RUN apt-get install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev -y
RUN apt-get install postgresql postgresql-contrib postgresql-client -y
RUN apt-get install libreadline-dev libffi-dev curl libbz2-dev libsqlite3-dev git unzip -y
RUN apt-get install wget libhdf5-dev libmecab-dev mecab-ipadic-utf8 liblzma-dev lzma -y
RUN apt-get install postgresql postgresql-contrib postgresql-client -y

# Install conceptnet
WORKDIR "/"
RUN git clone --single-branch --branch develop https://github.com/tae898/conceptnet5.git
WORKDIR "/conceptnet5"
RUN mkdir data
RUN mkdir conceptnet5/data

RUN pip install -U pip
RUN pip install -e .
RUN pip install wheel ipadic
RUN pip install -e '.[vectors]'
RUN pip install -e web


CMD ["python3", "web/conceptnet_web/api.py"]