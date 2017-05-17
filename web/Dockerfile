FROM rspeer/conceptnet:5.5.5
MAINTAINER Rob Speer <rob@luminoso.com>

# Install system dependencies (the overall form of this command is recommended by https://docs.docker.com/engine/userguide/eng-image/dockerfile_best-practices/)
RUN apt-get update \
  && apt-get install -y nginx supervisor \
  && rm -rf /var/lib/apt/lists/*

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
COPY server/nginx.conf /etc/nginx/conf.d/
# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY server/uwsgi.ini /etc/uwsgi/

COPY server/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN rm /etc/nginx/sites-enabled/default

## End of tiangolo/uwsgi-nginx-docker

RUN mkdir -p /data/nginx/cache
RUN mkdir -p /data/nginx/tmp

# Set up the local code
ADD conceptnet_web /src/conceptnet-web/conceptnet_web
ADD templates /src/conceptnet-web/templates
ADD setup.py /src/conceptnet-web/setup.py
ADD static /var/www/static

WORKDIR /src/conceptnet-web
RUN pip install -e '.'

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
