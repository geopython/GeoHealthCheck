#!/bin/bash
# Run unit tests in Docker Image
#
# Just van den Broecke - 2021
# Usage:
#   docker run  --entrypoint "/app/run-tests.sh" geopython/geohealthcheck:latest
#
echo "START run-tests.sh"

# Set the timezone.
# /set-timezone.sh
pushd /app || exit 1

source pixi-env.sh

# Configure: DB and plugins.
docker/scripts/configure.sh

# Make sure PYTHONPATH includes GeoHealthCheck
export PYTHONPATH=/app/GeoHealthCheck:${PYTHONPATH}

invoke run-tests

echo "END run-tests.sh"
