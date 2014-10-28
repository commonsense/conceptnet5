# This file is for serving ConceptNet 5.2's JSON API. There is a newer
# Docker build for 5.3 that serves both the API and the Web site.

FROM python:2.7
MAINTAINER Rob Speer <rob@luminoso.com>

# Python setup
RUN apt-get update
RUN apt-get install -y build-essential python-pip libatlas-dev liblapack-dev
RUN apt-get install -y gfortran

ENV LANG C.UTF-8

# Install Python dependencies using pip
RUN pip install numpy
RUN pip install gunicorn

ADD conceptnet5.2-legacy.tar.gz /src
ADD assoc-space-5.2.tar.gz /data
ADD debug-web.py /src/conceptnet5.2/debug-web.py

WORKDIR /src/conceptnet5.2
RUN mkdir -p /src/conceptnet5.2/logs

RUN python setup.py develop
ENV CONCEPTNET_ASSOC_DATA /data/assoc-space-5.2
ENTRYPOINT gunicorn -b 0.0.0.0:10052 --log-file - --access-logfile - -w 2 conceptnet5.api:app
