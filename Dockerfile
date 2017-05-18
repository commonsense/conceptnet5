FROM python:3.6
MAINTAINER Rob Speer <rob@luminoso.com>

# The ConceptNet package and its dependencies
# -------------------------------------------

# Configure the environment where ConceptNet will be built
ENV PYTHON python3

# Install system dependencies (the overall form of this command is recommended by https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/)
RUN apt-get update \
  && apt-get install -y build-essential python3-pip libatlas-dev liblapack-dev libhdf5-dev libmecab-dev mecab-ipadic-utf8 nginx supervisor \
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


# The ConceptNet web server
# -------------------------

## This stuff comes from tiangolo/uwsgi-nginx-docker:

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log
EXPOSE 80 443

# Set up uwsgi
RUN pip install uwsgi

# Make NGINX run on the foreground
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
# Copy the modified Nginx conf
COPY web/server/nginx.conf /etc/nginx/conf.d/
# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY web/server/uwsgi.ini /etc/uwsgi/

COPY web/server/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN rm /etc/nginx/sites-enabled/default

## End of tiangolo/uwsgi-nginx-docker

RUN mkdir -p /data/nginx/cache
RUN mkdir -p /data/nginx/tmp

# Set up the local code
ADD web/conceptnet_web /src/conceptnet-web/conceptnet_web
ADD web/templates /src/conceptnet-web/templates
ADD web/setup.py /src/conceptnet-web/setup.py
ADD web/static /var/www/static

WORKDIR /src/conceptnet-web
RUN pip install -e '.'

# Run the web server via its supervisor configuration
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

