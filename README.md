[![Build Status](https://travis-ci.org/geopython/GeoHealthCheck.png)](https://travis-ci.org/geopython/GeoHealthCheck)
[![Join the chat at https://gitter.im/geopython/GeoHealthCheck](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/geopython/GeoHealthCheck) 
[![Docker Build](https://img.shields.io/docker/automated/geopython/geohealthcheck.svg)](https://hub.docker.com/r/geopython/geohealthcheck)
[![Full Documentation](https://img.shields.io/badge/ReadTheDocs-online-green.svg)](http://docs.geohealthcheck.org)

GeoHealthCheck
==============

GeoHealthCheck (GHC) is a Service Status and QoS Checker for OGC Web Services and web APIs in general. 
See also the [full GHC documentation](http://docs.geohealthcheck.org/). 

Easiest is [to run GHC using Docker](https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md).
Below a quick overview of a manual install on Unix-based systems like Apple Mac and Linux.

```bash
python3 -m venv ghc_venv
. ghc_venv/bin/activate
git clone https://github.com/geopython/GeoHealthCheck.git
cd GeoHealthCheck
pip install .
# setup installation
geohc create-instance
# generate secret key
geohc create-secret-key
# setup local configuration (overrides GeoHealthCheck/config_main.py)
vi instance/config_site.py
# edit at least secret key:
# - SECRET_KEY  # copy/paste result string from geohc create-secret-key

# Optional: edit other settings or leave defaults
# - SQLALCHEMY_DATABASE_URI
# - GHC_RETENTION_DAYS
# - GHC_SELF_REGISTER
# - GHC_RUNNER_IN_WEBAPP
# - GHC_ADMIN_EMAIL
# - GHC_SITE_TITLE
# - GHC_MAP (or use default settings)

# setup database 
geohc db create

# create superuser account interactively
geohc db adduser

# start webserver with healthcheck runner daemon inside 
# (default is 0.0.0.0:8000)
geohc serve  
# or start webserver on another port
geohc serve -p 8881
# or start webserver on another IP
geohc serve -h 192.168.0.105 -p 8001

# OR start webserver and separate runner daemon (scheduler) process
vi instance/config_site.py
# GHC_RUNNER_IN_WEBAPP = False
geohc runner-daemon & 
geohc serve

# next: use a real webserver or preferably Docker for production

# other commands
#
# drop database
geohc db drop

# load data in database (WARN: deletes existing data!)
# See example data .json files in tests/data
geohc db load -f <.json data file> -y

# More help on the `geohc` cli command:
geohc --help

# More help on a specific command
geohc db load --help

```

**Note for developers:** instead of `pip install .`, you might want to install with the *editable*
option specified: `pip install -e .`

More in the [full GHC documentation](http://docs.geohealthcheck.org/).
