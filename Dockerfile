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

# Set up Gunicorn, which we'll use here for serving the API
RUN pip3 install gunicorn

# Download 5 GB of ConceptNet data
RUN make -e download_assertions

# Build the database (this takes about 8 hours)
RUN make -e build_db

# I don't believe that any of these steps can be parallelized, because
# they're bound by I/O.
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:10053", "conceptnet5.api:app"]
