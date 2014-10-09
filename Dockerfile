FROM rspeer/conceptnet-base:5.3b2
MAINTAINER Rob Speer <rob@luminoso.com>

# Configure the environment where ConceptNet will be built
ENV PYTHON python3
ADD conceptnet5 /src/conceptnet/conceptnet5
ADD tests /src/conceptnet/tests
ADD setup.py /src/conceptnet/setup.py
ADD Makefile /src/conceptnet/Makefile

# Set up ConceptNet
WORKDIR /src/conceptnet
RUN python3 setup.py develop
RUN pip3 install assoc_space==1.0b

# Download 5 GB of ConceptNet data
RUN make -e download_assertions

# Build the database (this takes about 8 hours)
RUN make -e build_db

# Get the association vectors
RUN make -e download_vectors

# Keep track of where the data ended up
ENV CONCEPTNET_DATA /src/conceptnet/data
