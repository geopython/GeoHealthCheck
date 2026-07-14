#!/bin/bash

echo "START run-runner.sh"

# Set the timezone.
# /set-timezone.sh
pushd /app || exit 1
source pixi-env.sh

# Configure: DB and plugins.
docker/scripts/configure.sh

# Make sure PYTHONPATH includes GeoHealthCheck
export PYTHONPATH=/app/GeoHealthCheck:$PYTHONPATH

invoke runner-daemon

echo "END run-runner.sh"
