#!/bin/bash

# Runs the GHC app with gunicorn

echo "START /run.sh"

cd /venv/ && . bin/activate

echo "Running GHC WSGI on ${HOST}:${PORT} with ${WSGI_WORKERS} workers"
cd /GeoHealthCheck
gunicorn --workers ${WSGI_WORKERS} \
		--worker-class=${WSGI_WORKER_CLASS} \
		--timeout ${WSGI_WORKER_TIMEOUT} \
		--name="Gunicorn_GHC" \
		--bind ${HOST}:${PORT} \
		GeoHealthCheck.app:APP

# Built-in Flask server, deprecated
# python /GeoHealthCheck/GeoHealthCheck/app.py ${HOST}:${PORT}

echo "END /run.sh"
