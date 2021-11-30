#Download base image ubuntu 20.04
FROM ubuntu:20.04

LABEL maintainer="mmachado@ibm.com"

LABEL description="This is custom Docker Image for Conceptnet 5."

#RUN apt-get install postgresql-10 -y

#Define the ENV variable
# ENV CONCEPTNET_DB_PASSWORD=
ENV CONCEPTNET_DATA=/conceptnet_data

RUN apt-get update
RUN apt-get install -y build-essential python3-pip python3-dev libhdf5-dev libmecab-dev mecab-ipadic-utf8

COPY . /usr/src
WORKDIR /usr/src

RUN mkdir conceptnet5/data

RUN pip install -U pip
RUN pip install -e .
RUN pip install -e '.[vectors]'
RUN pip install -e web

RUN chown -R 1001:0 /usr/src
USER 1001

WORKDIR /usr/src/web
CMD ["python3", "conceptnet_web/api.py"]