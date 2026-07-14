#!/bin/bash


# Copy possible mounted Plugins into app tree
if [ -d /plugins ]
then
	cp -ar /plugins/* /app/GeoHealthCheck/plugins/
fi

python3 /app/GeoHealthCheck/healthcheck.py
