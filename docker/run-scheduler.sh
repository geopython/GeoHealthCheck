# /bin/bash

# Run the GHC daemon process that schedules healthcheck jobs
source /venv/bin/activate .
cd /GeoHealthCheck
paver runner_daemon


