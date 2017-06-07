#!/bin/bash

cd /
virtualenv venv && cd $_
. bin/activate

# To be Removed as to enable local and versioned (tagged) images builds
cd /
git clone ${GHC_GIT_REPO} GeoHealthCheck

# GHC Source was ADDed in Dockerfile
cd /GeoHealthCheck
pip install Paver
pip install sphinx

# For PostGIS support
pip install psycopg2

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

