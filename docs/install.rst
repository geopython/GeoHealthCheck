.. _install:

Installation
============

Quick and Dirty
---------------

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
  # - GHC_RUN_FREQUENCY
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

  # start server
  python GeoHealthCheck/app.py  # http://localhost:8000/



Requirements
------------

GeoHealthCheck is built on the awesome Flask microframework and uses
Flask-SQLAlchemy for database interaction and Flask-Login for authorization.
Flask-Migrate with Alembic and Flask-Script support is used for database upgrades.

OWSLib is used to interact with OGC Web Services.

Install
-------

.. note::

  it is strongly recommended to install in a Python ``virtualenv``.
  a ``virtualenv`` is self-contained and provides the flexibility to install /
  tear down / whatever packages without affecting system wide packages or
  settings.

- Download GeoHealthCheck (releases can be found at
  https://github.com/geopython/GeoHealthCheck/releases)

Upgrade
-------

An existing GHC database installation can be upgraded with:

.. code-block:: bash

  # In the top directory (e.g. the topdir cloned from github)
  paver upgrade

  # Notice any output, in particular errors

Notes:

* **Always backup your database first!!**
* upgrading should be "smart": only performed when required


Running
-------

Start using the built-in ``mod_wsgi`` server:

.. code-block:: bash

  python GeoHealthCheck/app.py  # http://localhost:8000
  python GeoHealthCheck/app.py 0.0.0.0:8881  # http://localhost:8881
  python GeoHealthCheck/app.py 192.168.0.105:8957  # http://192.168.0.105:8957


To enable in Apache, use ``GeoHealthCheck.wsgi`` and configure in Apache
as per the main Flask documentation.

