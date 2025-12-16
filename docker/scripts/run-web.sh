#!/bin/bash

# Runs the GHC app with gunicorn

echo "START /run-web.sh"

# Set the timezone.
# /set-timezone.sh

# Configure: DB and plugins.
/configure.sh

# Make sure PYTHONPATH includes GeoHealthCheck
export PYTHONPATH=/GeoHealthCheck/GeoHealthCheck:$PYTHONPATH

pushd /GeoHealthCheck || exit 1

source bin/activate

paver upgrade

# SCRIPT_NAME should not have value '/'
[ "${SCRIPT_NAME}" = '/' ] && export SCRIPT_NAME="" && echo "make SCRIPT_NAME empty from /"

echo "Running GHC WSGI on ${HOST}:${PORT} with ${WSGI_WORKERS} workers and SCRIPT_NAME=${SCRIPT_NAME}"
exec gunicorn --pythonpath /GeoHealthCheck/lib/python3.12/site-packages/ --workers ${WSGI_WORKERS} \
		--worker-class=${WSGI_WORKER_CLASS} \
		--timeout ${WSGI_WORKER_TIMEOUT} \
		--name="Gunicorn_GHC" \
		--bind ${HOST}:${PORT} \
		GeoHealthCheck.app:APP

# Built-in Flask server, deprecated
# python /GeoHealthCheck/GeoHealthCheck/app.py ${HOST}:${PORT}

echo "END /run-web.sh"
