#!/bin/bash

cd /
virtualenv venv && cd $_
. bin/activate

# GHC Source was ADDed in Dockerfile
cd /GeoHealthCheck
pip install Paver
pip install sphinx

# For PostGIS support
pip install psycopg2

# For WSGI server
# NB we use async workers as some Probes may take a long time
# e.g. fetching Metadata (Caps) and testing all layers
pip install -I eventlet
pip install -I gunicorn

# Sets up GHC itself
paver setup
mv /config_site.py /GeoHealthCheck/instance/config_site.py

# Copy possible Plugins into app tree
if [ -d /plugins ]
then
	# Copy possible Plugins into app tree
	cp -ar /plugins/* GeoHealthCheck/plugins/

	# Remove to allow later Volume mount of /plugins
	rm -rf /plugins
fi

