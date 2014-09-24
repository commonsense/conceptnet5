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
RUN python3 setup.py develop

# Download 10.8 GB of input data
RUN make -e download

# Build ConceptNet. On 6 cores (which is what -j6 configures it for here),
# this takes about 13 hours for me. The resulting image will take up about
# 50 GB of disk space.
RUN make -e -j6 all
