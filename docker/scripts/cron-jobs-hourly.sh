#!/bin/bash


# Copy possible mounted Plugins into app tree
if [ -d /plugins ]
then
	cp -ar /plugins/* /GeoHealthCheck/GeoHealthCheck/plugins/
fi

python3 /GeoHealthCheck/GeoHealthCheck/healthcheck.py
