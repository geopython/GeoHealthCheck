#!/bin/bash

echo "START /run-runner.sh"

# Set the timezone.
# /set-timezone.sh

# Configure: DB and plugins.
/configure.sh

# Make sure PYTHONPATH includes GeoHealthCheck
export PYTHONPATH=/GeoHealthCheck/GeoHealthCheck:$PYTHONPATH

cd /GeoHealthCheck
paver runner_daemon

echo "END /run-runner.sh"
