FROM rspeer/conceptnet-env:5.4
MAINTAINER Rob Speer <rob@luminoso.com>

# Configure the environment where ConceptNet will be built
ENV PYTHON python3
ADD conceptnet5 /src/conceptnet/conceptnet5
ADD tests /src/conceptnet/tests
ADD rules.ninja /src/conceptnet/rules.ninja
ADD ninja.py /src/conceptnet/ninja.py
ADD setup.py /src/conceptnet/setup.py
ADD Makefile /src/conceptnet/Makefile

# Set up ConceptNet
WORKDIR /src/conceptnet
RUN python3 setup.py develop
RUN python3 ninja.py
RUN ninja -v

