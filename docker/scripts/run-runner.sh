#!/bin/bash

echo "START /run-runner.sh"

# Set the timezone.
/set-timezone.sh

# Configure: DB and plugins.
/configure.sh

# Run the GHC daemon process
# that schedules healthcheck jobs
source /venv/bin/activate .

geohc runner-daemon

echo "END /run-runner.sh"
