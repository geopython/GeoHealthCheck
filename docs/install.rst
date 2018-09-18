.. _install:

Installation
============

Below are installation notes for GeoHealthCheck (GHC).

Docker
------

The easiest and quickest install
for GHC is with Docker/Docker Compose using the GHC images hosted on
`Docker Hub <https://hub.docker.com/r/geopython/geohealthcheck>`_.

See the
`GHC Docker Readme <https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md>`_
for a full guide.

Requirements
------------

GeoHealthCheck is built on the awesome Flask micro-framework and uses
`Flask-SQLAlchemy` for database interaction and Flask-Login for authorization.
`Flask-Migrate` with `Alembic` and `Flask-Script` is used for database upgrades.

`OWSLib` is used to interact with OGC Web Services.

`APScheduler` is used to run scheduled healthchecks.

These dependencies are automatically installed (see below). ``Paver`` is used
for installation and management. ``Cron`` was used for scheduling the actual
healthchecks before v0.4.0.

Install
-------

.. note::

  It is strongly recommended to install GeoHealthCheck in a Python ``virtualenv``.
  a ``virtualenv`` is self-contained and provides the flexibility to install /
  tear down / whatever packages without affecting system wide packages or
  settings.
  If installing on Ubuntu, you may need to install the python-dev package for installation to complete successfully.
  
- Download a GeoHealthCheck release from
  https://github.com/geopython/GeoHealthCheck/releases, or clone manually from GitHub. 

.. code-block:: bash

  virtualenv ghc && cd ghc
  . bin/activate
  git clone https://github.com/geopython/GeoHealthCheck.git
  cd GeoHealthCheck

  # install paver dependency for admin tool
  pip install Paver

  # setup app
  paver setup

  # create secret key to use for auth
  paver create_secret_key

  # almost there!  Customize config
  vi instance/config_site.py
  # edit:
  # - SQLALCHEMY_DATABASE_URI
  # - SECRET_KEY  # from paver create_secret_key
  # - GHC_RETENTION_DAYS
  # - GHC_SELF_REGISTER
  # - GHC_NOTIFICATIONS
  # - GHC_NOTIFICATIONS_VERBOSITY
  # - GHC_ADMIN_EMAIL
  # - GHC_NOTIFICATIONS_EMAIL
  # - GHC_SITE_TITLE
  # - GHC_SITE_URL
  # - GHC_SMTP  # if GHC_NOTIFICATIONS is enabled
  # - GHC_MAP  # or use default settings

  # init database
  python GeoHealthCheck/models.py create

  # start web-app
  python GeoHealthCheck/app.py  # http://localhost:8000/

Schedule the cronjobs.

.. code-block:: bash

  # edit local paths to scripts
  vi jobs.cron

  # enable cron
  crontab jobs.cron

.. _upgrade:

Upgrade
-------

An existing GHC database installation can be upgraded with:

.. code-block:: bash

  # In the top directory (e.g. the topdir cloned from github)
  paver upgrade

  # Notice any output, in particular errors

Notes:

* **Always backup your database first!!**
* make sure Flask-Migrate is installed (see requirements.txt), else:  `pip install Flask-Migrate==2.0.3`, but best is to run `paver setup` also for other dependencies
* upgrading is "smart": you can always run `paver upgrade`, it has no effect when DB already uptodate
* when upgrading from earlier versions without Plugin-support

  - adapt your `config_site.py` to Plugin settings from `config_main.py`
  - assign `Probes` and `Checks` to each `Resource` via the UI

When running with Docker see the
`GHC Docker Readme <https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md>`_
how to run `paver upgrade` within your Docker Container.

Running
-------

Start using the built-in ``mod_wsgi`` server:

.. code-block:: bash

  python GeoHealthCheck/app.py  # http://localhost:8000
  python GeoHealthCheck/app.py 0.0.0.0:8881  # http://localhost:8881
  python GeoHealthCheck/app.py 192.168.0.105:8957  # http://192.168.0.105:8957


To enable in Apache, use ``GeoHealthCheck.wsgi`` and configure in Apache
as per the main Flask documentation.

