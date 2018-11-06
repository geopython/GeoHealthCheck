#!/bin/bash

cd /
virtualenv venv && cd /venv
. bin/activate

# GHC Source was added in Dockerfile, install
# NB we use gunicorn/eventlet async workers as some Probes may take a long time
# e.g. fetching Metadata (Caps) and testing all layers
# Install Python packages for installation and setup
pip install -I -r /GeoHealthCheck/docker/scripts/requirements.txt

cd /GeoHealthCheck

# Sets up GHC itself
paver setup
mv /config_site.py /GeoHealthCheck/instance/config_site.py

# Copy possible Plugins into app tree
if [ -d /plugins ]
then
	# Copy possible Plugins into app tree
	echo "Installing Plugins..."
	cp -ar /plugins/* GeoHealthCheck/plugins/

	# Remove to allow later Volume mount of /plugins
	rm -rf /plugins
fi

