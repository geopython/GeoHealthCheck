#!/bin/bash

# Runs the GHC app with gunicorn

echo "START run-web.sh"

# Set the timezone.
# /set-timezone.sh
pushd /app || exit 1
source pixi-env.sh

# Configure: DB and plugins.
docker/scripts/configure.sh

# Make sure PYTHONPATH includes GeoHealthCheck
export PYTHONPATH=/app/GeoHealthCheck:$PYTHONPATH

# pixi shell -e prod
invoke db-action upgrade

# SCRIPT_NAME should not have value '/'
[ "${SCRIPT_NAME}" = '/' ] && export SCRIPT_NAME="" && echo "make SCRIPT_NAME empty from /"

echo "Running GHC WSGI on ${HOST}:${PORT} with ${WSGI_WORKERS} workers and SCRIPT_NAME=${SCRIPT_NAME}"
gunicorn --workers ${WSGI_WORKERS} \
		--worker-class=${WSGI_WORKER_CLASS} \
		--timeout ${WSGI_WORKER_TIMEOUT} \
		--chdir ${GHC_USER_HOME} \
		--name="Gunicorn_GHC" \
		--bind ${HOST}:${PORT} \
		GeoHealthCheck.app:APP

# Built-in Flask server, deprecated
# python3 /app/GeoHealthCheck/app.py ${HOST}:${PORT}

echo "END run-web.sh"
