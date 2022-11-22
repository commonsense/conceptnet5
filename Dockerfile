FROM ubuntu:20.04 as base

LABEL maintainer="mmachado@ibm.com"

LABEL description="This is a custom Docker Image for Conceptnet 5."

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update

#basics
RUN apt-get install git curl wget unzip build-essential -y

# python
RUN apt-get install python3-pip python3-dev -y

#etc
RUN apt-get install postgresql-client -y
RUN apt-get install zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev -y
RUN apt-get install libreadline-dev libbz2-dev libsqlite3-dev liblzma-dev lzma -y

# Conceptnet required libs
RUN apt-get install libhdf5-dev libmecab-dev mecab-ipadic-utf8 -y

RUN pip install -U pip
RUN pip install pytest PyLD language_data wheel ipadic

# Install conceptnet
WORKDIR "/"

COPY . /usr/src

WORKDIR /usr/src

RUN mkdir data

RUN pip install -e . 
RUN pip install -e '.[vectors]'
RUN pip install -e web


EXPOSE 8084

FROM base as debug

RUN pip install debugpy
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1


FROM base as prod

CMD python3 web/conceptnet_web/api.py