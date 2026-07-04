#!/bin/bash

# GHC source was added in the Dockerfile; set up the pixi environment.
# NB we use gunicorn/gevent async workers as some Probes may take a long time
# e.g. fetching Metadata (Caps) and testing all layers.
set -e

cd /GeoHealthCheck || exit 1

# Create the locked `prod` environment: Python plus all app/runtime deps
# (incl. gunicorn/gevent, lxml, pyproj, invoke) from conda-forge/PyPI.
pixi install --locked -e prod

# Bootstrap GHC itself: static JS assets, i18n .mo files, local docs, dirs.
pixi run -e prod setup

# Use the Docker-specific site config (overrides the default from setup).
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
