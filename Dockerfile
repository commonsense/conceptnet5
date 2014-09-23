FROM rspeer/conceptnet-env:5.3b1
MAINTAINER Rob Speer <rob@luminoso.com>

# Configure the environment where ConceptNet will be built
ENV PYTHON python3
ADD conceptnet5 /src/conceptnet/conceptnet5
ADD tests /src/conceptnet/tests
ADD setup.py /src/conceptnet/setup.py
ADD Makefile /src/conceptnet/Makefile

# Set up ConceptNet
WORKDIR /src/conceptnet
RUN pip3 install -e .

# Build ConceptNet on the /data volume
RUN make -e download
RUN make -e -j6 all
