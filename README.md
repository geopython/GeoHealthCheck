[![Build Status](https://travis-ci.org/geopython/GeoHealthCheck.png)](https://travis-ci.org/geopython/GeoHealthCheck)
[![Join the chat at https://gitter.im/geopython/GeoHealthCheck](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/geopython/GeoHealthCheck) 
[![Docker Build](https://github.com/geopython/GeoHealthCheck/actions/workflows/docker.yml/badge.svg)](https://github.com/geopython/GeoHealthCheck/actions/workflows/docker.yml)
[![Full Documentation](https://img.shields.io/badge/ReadTheDocs-online-green.svg)](http://docs.geohealthcheck.org)

GeoHealthCheck
==============

GeoHealthCheck (GHC) is a Service Status and QoS Checker for OGC Web Services and web APIs in general. 
See also the [full GHC documentation](http://docs.geohealthcheck.org/). 

Easiest is [to run GHC using Docker](https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md).
Below a quick overview of a manual install on Unix-based systems like Apple MacOS and Linux.

```bash
virtualenv GeoHealthCheck && cd $_
. bin/activate
git clone https://github.com/geopython/GeoHealthCheck.git
cd GeoHealthCheck
pip install Paver
# setup installation
paver setup
# generate secret key
paver create_secret_key
# setup local configuration (overrides GeoHealthCheck/config_main.py)
vi instance/config_site.py
# edit at least secret key:
# - SECRET_KEY  # copy/paste result string from paver create_secret_key

# Optional: edit other settings or leave defaults
# - SQLALCHEMY_DATABASE_URI
# - GHC_RETENTION_DAYS
# - GHC_SELF_REGISTER
# - GHC_RUNNER_IN_WEBAPP
# - GHC_ADMIN_EMAIL
# - GHC_SITE_TITLE
# - GHC_MAP (or use default settings)

# setup database and superuser account interactively 
paver create

# start webserver with healthcheck runner daemon inside 
# (default is 0.0.0.0:8000)
python GeoHealthCheck/app.py  
# or start webserver on another port
python GeoHealthCheck/app.py 0.0.0.0:8881
# or start webserver on another IP
python GeoHealthCheck/app.py 192.168.0.105:8001

# OR start webserver and separate runner daemon (scheduler) process
vi instance/config_site.py
# GHC_RUNNER_IN_WEBAPP = False
python GeoHealthCheck/scheduler.py & 
python GeoHealthCheck/app.py  

# next: use a real webserver or preferably Docker for production

# other commands
#
# drop database
python GeoHealthCheck/models.py drop

# load data in database (WARN: deletes existing data!)
# See example data .json files in tests/data
python GeoHealthCheck/models.py load <.json data file> [y/n]

```

More in the [full GHC documentation](http://docs.geohealthcheck.org/).
