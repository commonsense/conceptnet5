FROM rspeer/conceptnet-base:5.4
MAINTAINER Rob Speer <rob@luminoso.com>

# Configure the environment where ConceptNet will be built
ENV PYTHON python3
ADD conceptnet5 /src/conceptnet/conceptnet5
ADD tests /src/conceptnet/tests
ADD setup.py /src/conceptnet/setup.py
ADD ninja.py /src/conceptnet/ninja.py
ADD rules.ninja /src/conceptnet/rules.ninja

# Set up ConceptNet
WORKDIR /src/conceptnet
RUN python3 setup.py develop
RUN pip3 install assoc_space==1.0b
RUN pip3 install wordfreq==1.0b4

# Run the ninja build
RUN python3 ninja.py
RUN ninja -v

# Keep track of where the data ended up
ENV CONCEPTNET_DATA /src/conceptnet/data
