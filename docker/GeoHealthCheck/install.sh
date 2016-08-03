#!/bin/bash

cd /
virtualenv venv && cd $_
. bin/activate
cd /
git clone https://github.com/geopython/GeoHealthCheck.git
cd /GeoHealthCheck
pip install Paver
pip install sphinx
paver setup
mv /config_site.py /GeoHealthCheck/instance/config_site.py
