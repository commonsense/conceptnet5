#!/bin/sh
export LUMINOSO_DATA=/srv/conceptnet5.1/lumi_data
gunicorn -b 0.0.0.0:8087 -w 1 conceptnet5.api:app
