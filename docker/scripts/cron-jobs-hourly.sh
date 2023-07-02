#!/bin/bash


# Copy possible mounted Plugins into app tree
if [ -d /plugins ]
then
	cp -ar /plugins/* /GeoHealthCheck/GeoHealthCheck/plugins/
fi

python /GeoHealthCheck/GeoHealthCheck/healthcheck.py
