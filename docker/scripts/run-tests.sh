#!/bin/bash
# Run unit tests in Docker Image
#
# Just van den Broecke - 2021
# Usage:
#   docker run  --entrypoint "/run-tests.sh" geopython/geohealthcheck:latest
#
echo "START /run-tests.sh"

# Set the timezone.
# /set-timezone.sh

# Configure: DB and plugins.
/configure.sh

# Make sure PYTHONPATH includes GeoHealthCheck
export PYTHONPATH=/GeoHealthCheck/GeoHealthCheck:$PYTHONPATH

cd /GeoHealthCheck
source bin/activate
paver run_tests

echo "END /run-tests.sh"
