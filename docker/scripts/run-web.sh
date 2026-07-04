#!/bin/bash

# Runs the GHC app with gunicorn (from the pixi `prod` env)

echo "START /run-web.sh"

# Set the timezone.
# /set-timezone.sh

# Configure: DB and plugins.
/configure.sh

# Make sure PYTHONPATH includes GeoHealthCheck (for intra-package imports)
export PYTHONPATH=/GeoHealthCheck/GeoHealthCheck:$PYTHONPATH

cd /GeoHealthCheck || exit 1

pixi run -e prod invoke upgrade

# SCRIPT_NAME should not have value '/'
[ "${SCRIPT_NAME}" = '/' ] && export SCRIPT_NAME="" && echo "make SCRIPT_NAME empty from /"

echo "Running GHC WSGI on ${HOST}:${PORT} with ${WSGI_WORKERS} workers and SCRIPT_NAME=${SCRIPT_NAME}"
exec pixi run -e prod gunicorn --chdir /GeoHealthCheck --workers ${WSGI_WORKERS} \
		--worker-class=${WSGI_WORKER_CLASS} \
		--timeout ${WSGI_WORKER_TIMEOUT} \
		--name="Gunicorn_GHC" \
		--bind ${HOST}:${PORT} \
		GeoHealthCheck.app:APP

# Built-in Flask server, deprecated
# python3 /GeoHealthCheck/GeoHealthCheck/app.py ${HOST}:${PORT}

echo "END /run-web.sh"
