FROM rspeer/conceptnet-base:5.4
MAINTAINER Rob Speer <rob@luminoso.com>

# Configure the environment where ConceptNet will be built
ENV PYTHON python3
ADD conceptnet5 /src/conceptnet/conceptnet5
ADD tests /src/conceptnet/tests
ADD setup.py /src/conceptnet/setup.py
ADD Snakefile /src/conceptnet/Snakefile

# Set up ConceptNet
WORKDIR /src/conceptnet
RUN python3 setup.py develop
RUN pip3 install assoc_space==1.0.2
RUN pip3 install wordfreq==1.0
RUN python -c 'import nltk; nltk.download("wordnet")'

# This is where the data should go, but you have to put it there using
# a Docker volume
ENV CONCEPTNET_DATA /conceptnet_data

ENTRYPOINT /bin/bash
