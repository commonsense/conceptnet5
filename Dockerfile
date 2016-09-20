FROM python:3.5
MAINTAINER Rob Speer <rob@luminoso.com>

# Configure the environment where ConceptNet will be built
ENV PYTHON python3

# Install system dependencies (the overall form of this command is recommended by https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/)
RUN apt-get update \
  && apt-get install -y build-essential python3-pip libatlas-dev liblapack-dev libhdf5-dev \
  && rm -rf /var/lib/apt/lists/*

ADD conceptnet5 /src/conceptnet/conceptnet5
ADD tests /src/conceptnet/tests
ADD scripts /src/conceptnet/scripts
ADD testdata /src/conceptnet/testdata
ADD setup.py /src/conceptnet/setup.py
ADD Snakefile /src/conceptnet/Snakefile

# Set up ConceptNet, with optional dependencies for conceptnet5.vectors
WORKDIR /src/conceptnet
RUN pip install -e '.[vectors]'

# This is where the data should go, but you have to put it there using
# a Docker volume
ENV CONCEPTNET_DATA /conceptnet_data

RUN /bin/bash
