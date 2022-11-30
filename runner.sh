#!/bin/bash

if [ -z ${UWSGI_INI+x} ];
then
  export UWSGI_INI=uwsgi.ini
fi

export PYTHONPATH="$PYTHONPATH:${PWD}"

while true; do
  case "$1" in
    standalone)
        python3 ./web/conceptnet_web/api.py
        ;;
    *)
        uwsgi
        ;;
  esac

  echo "WILL RESTART PROCESS!!!"
done
