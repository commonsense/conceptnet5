FROM rspeer/conceptnet:5.4
MAINTAINER Rob Speer <rob@luminoso.com>

RUN pip install gunicorn

ADD router/static /src/conceptnet/static
ADD templates /src/conceptnet/templates
ADD wsgi_web.py /src/conceptnet/wsgi_web.py

ENV CONCEPTNET_DATA /conceptnet_data
ENV CONCEPTNET_WEB_STATIC /src/conceptnet/static
ENV CONCEPTNET_WEB_TEMPLATES /src/conceptnet/templates
ENTRYPOINT gunicorn -b 0.0.0.0:10054 --log-file - --access-logfile - -w 4 wsgi_web:application
