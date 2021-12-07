# Start from the official postgres image
FROM postgres

LABEL maintainer="mmachado@ibm.com"

LABEL description="This is custom Docker Image for Conceptnet 5."
# Adding the below environment variables allow you to create a database easily within 
# the docker contianer

ARG DEBIAN_FRONTEND=noninteractive
ARG CONCEPTNET_DB_NAME=conceptnet5
ARG CONCEPTNET_DB_USER=postgres
ARG CONCEPTNET_DB_HOSTNAME=0.0.0.0	
ARG CONCEPTNET_DB_PASSWORD
ARG CONCEPTNET_DB_PORT=5432

ENV POSTGRES_USER=${CONCEPTNET_DB_USER}
ENV POSTGRES_PASSWORD=${CONCEPTNET_DB_PASSWORD}
ENV POSTGRES_DB=${CONCEPTNET_DB_NAME}

# Install the necessary libraries for both postgres and conceptnet
RUN apt update
RUN apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev -y
RUN apt install postgresql postgresql-contrib postgresql-client -y
RUN apt install libreadline-dev libffi-dev curl libbz2-dev libsqlite3-dev git unzip -y
RUN apt install wget libhdf5-dev libmecab-dev mecab-ipadic-utf8 liblzma-dev lzma -y

# Install python 3.7.12
# Somehow I couldn't just `apt install python3.7`. Here I manually download and compile it.
RUN wget https://www.python.org/ftp/python/3.7.12/Python-3.7.12.tgz
RUN tar -xf Python-3.7.12.tgz
WORKDIR "/Python-3.7.12"
RUN ./configure --enable-optimizations --enable-loadable-sqlite-extensions
RUN make -j$(nproc)
RUN make install
RUN apt install python3-pip python3-dev  -y

# Install conceptnet
WORKDIR "/"
RUN git clone --single-branch --branch develop https://github.com/tae898/conceptnet5.git
WORKDIR "/conceptnet5"
RUN mkdir data
# modify `build.sh` in place to speed up processing
RUN pip3 install --upgrade pip
RUN pip3 install wheel ipadic
RUN pip3 install -e '.[vectors]'
RUN pip install -e web

CMD [ "postgres" ]