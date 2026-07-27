[![CI Build](https://github.com/geopython/GeoHealthCheck/actions/workflows/main.yml/badge.svg)](https://github.com/geopython/GeoHealthCheck/actions/workflows/main.yml)
[![Docker Build](https://github.com/geopython/GeoHealthCheck/actions/workflows/docker.yml/badge.svg)](https://github.com/geopython/GeoHealthCheck/actions/workflows/docker.yml)
[![Full Documentation](https://img.shields.io/badge/ReadTheDocs-online-green.svg)](https://docs.geohealthcheck.org)
[![Gitter](https://img.shields.io/gitter/room/geopython/GeoHealthCheck.svg?style=flat-square)](https://gitter.im/geopython/GeoHealthCheck)

# GeoHealthCheck

GeoHealthCheck (GHC) is a Service Status and QoS Checker for OGC Web Services and web APIs in general. 
See also the [full GHC documentation](http://docs.geohealthcheck.org/). 

Easiest is [to run GHC using Docker](https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md).

## Standard Install

Below an overview of an installation on Unix-based systems like Apple MacOS and Linux with just plain Python. 
NB works with Python 3.12.*, other Python versions need tweaking [pyproject.toml](pyproject.toml).

```bash

python -m venv ghc && cd ghc
. bin/activate
git clone https://github.com/geopython/GeoHealthCheck.git
cd GeoHealthCheck
pip install --no-cache-dir -U pip setuptools wheel Invoke
pip install --no-cache-dir -e . 

# setup installation
invoke setup
# generate secret key
invoke create-secret-key
# setup local configuration (overrides GeoHealthCheck/config_main.py)
vi instance/config_site.py
# edit at least secret key:
# - SECRET_KEY  # copy/paste result string from `invoke create-secret-key`
# - SQLALCHEMY_DATABASE_URI = 'sqlite:///../instance/data.db' - put in instance dir

# Optional: edit other settings or leave defaults
# - SQLALCHEMY_DATABASE_URI
# - GHC_RETENTION_DAYS
# - GHC_SELF_REGISTER
# - GHC_RUNNER_IN_WEBAPP
# - GHC_ADMIN_EMAIL
# - GHC_SITE_TITLE
# - GHC_MAP (or use default settings)

# setup database and superuser account interactively 
invoke create -u admin -p admin -e a@a.com

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

## Install with Pixi

[Pixi](https://pixi.sh) manages the environment; tasks run via `pixi run`,
so no shell activation is needed.

```bash

git clone https://github.com/geopython/GeoHealthCheck.git
cd GeoHealthCheck

# Install production environment
pixi install -e prod

# bootstrap the app (config, static assets, i18n, local docs, DB)
pixi run -e prod setup

# generate secret key
pixi run -e prod create-secret-key
# setup local configuration (overrides GeoHealthCheck/config_main.py)
vi instance/config_site.py
# edit at least secret key:
# - SECRET_KEY  # copy/paste result string from the command above

# Optional: edit other settings or leave defaults (see above)

# setup superuser account password and email directly
pixi run -e prod create --username admin --password admin --email a@a.com

# or shorter
pixi run -e prod create -u admin -p admin --e a@a.com

# run locally
pixi run -e prod run
 
# open http://localhost:8000 in browser

```

### Development and tests

```bash

# install the dev environment (adds flake8, pytest, ...)
pixi install -e dev

# bootstrap once, needed before the tests can run
pixi run -e dev setup

# run the unit tests
pixi run -e dev test
```

Prefer an interactive shell? `pixi shell -e prod` (or `-e dev`) activates the
environment, after which `invoke ...` and `python ...` work directly.


More in the [full GHC documentation](http://docs.geohealthcheck.org/).
