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
healthchecks before v0.5.0.

Starting from version v0.8.0.0 GeoHealthCheck requires **python 3**. Previous
versions require **python 2**.

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

  python3 -m venv ghc && cd ghc
  source ghc/bin/activate
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
  # - GHC_RUNNER_IN_WEBAPP # see 'running' section below
  # - GHC_REQUIRE_WEBAPP_AUTH  # optional: to require authentication to access webapp
  # - GHC_SMTP  # if GHC_NOTIFICATIONS is enabled
  # - GHC_MAP  # or use default settings
  # - GEOIP  # or use the feault settings

  # init database
  python GeoHealthCheck/models.py create

  # start web-app
  python GeoHealthCheck/app.py  # http://localhost:8000/

  # when you are done, you can exit the virtualenv
  deactivate

NB GHC supports internal scheduling, no cronjobs required.

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
* make sure Flask-Migrate is installed (see requirements.txt), else:  `pip install Flask-Migrate==2.5.2`, but best is to run `paver setup` also for other dependencies
* upgrading is "smart": you can always run `paver upgrade`, it has no effect when DB is already up to date
* when upgrading from earlier versions without Plugin-support:

  - adapt your `config_site.py` to Plugin settings from `config_main.py`
  - assign `Probes` and `Checks` to each `Resource` via the UI

When running with Docker see the
`Docker Readme <https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md>`_
how to run `paver upgrade` within your Docker Container.

Upgrade notes v0.5.0
....................

In GHC v0.5.0 a new run-architecture was introduced. By default, healthchecks run under
the control of an internal scheduler, i.s.o. of external cron-jobs. See also the :ref:`architecture` chapter
and :ref:`admin_running` and below.

Upgrade notes v0.6.0
....................

In GHC v0.6.0 encryption was added for password storage. Existing passwords should be migrated via
the `paver upgrade` command. Also password recovery was changed: a user can create a new password via
a unique, personal URL that GHC sends by email. This requires a working email configuration and a reachable
`SITE_URL` config value. See :ref:`admin_user_mgt` for solving password problems.

See `closed issues for related Milestone 0.6.0 <https://github.com/geopython/GeoHealthCheck/milestone/6?closed=1>`_

Upgrade notes v0.7.0
....................

No database changes. Many fixes and enhancements, see `closed issues for related Milestone 0.7.0 <https://github.com/geopython/GeoHealthCheck/milestone/7?closed=1>`_.

Upgrade notes v0.8.0
....................

Main change: migrated from Python 2 to Python 3. No DB upgrades required.
One major improvement was more robust (HTTP) retries using the `requests` `Session` object.

See `closed issues for related Milestone 0.8.0 <https://github.com/geopython/GeoHealthCheck/milestone/8?closed=1>`_.

Upgrade notes v0.8.2
....................

Main change: Bugfixes and small new features on 0.8.0 (0.8.1 was skipped). No DB upgrades required.

OWSLib was upgraded to 0.20.0. Some Py2 to Py3 string encoding issues.

One major improvement was adding `User-Agent` HTTP header for Probe requests.

See `closed issues for related Milestone 0.8.2 <https://github.com/geopython/GeoHealthCheck/milestone/9?closed=1>`_.

Running
-------

Start using Flask's built-in WSGI server:

.. code-block:: bash

  python GeoHealthCheck/app.py  # http://localhost:8000
  python GeoHealthCheck/app.py 0.0.0.0:8881  # http://localhost:8881
  python GeoHealthCheck/app.py 192.168.0.105:8957  # http://192.168.0.105:8957


This runs the (Flask) **GHC Webapp**, by default with the **GHC Runner** (scheduled healthchecker) internally.
See also :ref:`admin_running` for the different options running the **GHC Webapp** and **GHC Runner**. It is
recommended to run these as separate processes. For this set **GHC_RUNNER_IN_WEBAPP** to `False` in your `site_config.py`.
From the command-line run both processes, e.g. in background or different terminal sessions:

.. code-block:: bash

  # run GHC Runner, here in background
  python GeoHealthCheck/scheduler.py &

  # run GHC Webapp for http://localhost:8000
  python GeoHealthCheck/app.py


To enable in Apache, use ``GeoHealthCheck.wsgi`` and configure in Apache
as per the main Flask documentation.

Running under a sub-path
------------------------

By default GeoHealthCheck is configured to run under the root directory on the webserver. However, it can be configured to run under a sub-path. The method for doing this depends on the webserver you are using, but the general requirement is to pass Flask's ``SCRIPT_NAME`` environment variable when GeoHealthCheck is started. 

Below is an example of how to use nginx and gunicorn to run GeoHealthCheck in a directory "geohealthcheck", assuming that you have nginx and gunicorn already set up and configured:

- In nginx add a section to the server block you are running GeoHealthCheck under:
 
.. code-block:: bash
 
    location /geohealthcheck {
      proxy_pass http://127.0.0.1:8000/geohealthcheck;
    }
      
- Include the parameter "-e SCRIPT_NAME=/geohealthcheck" in your command for running gunicorn:

.. code-block:: bash
  
    gunicorn -e SCRIPT_NAME=/geohealthcheck app:app

Production Recommendations
--------------------------

Use Docker!
...........

When running GHC in long-term production environment the following is recommended:

* use Docker, see the `GHC Docker Readme <https://github.com/geopython/GeoHealthCheck/tree/master/docker>`_

Using Docker, especially with Docker Compose (sample files provided) is our #1 recommendation. It saves
all the hassle from installing the requirements, upgrades etc. Docker (Compose) is also used to run the GHC demo site
and almost all of our other deployments.

Use PostgreSQL
..............

Although GHC will work with `SQLite`, this is not a good option for production use, in particular
for reliability starting with GHC v0.5.0:

* reliability:  **GHC Runner** will do concurrent updates to the database, this will be unreliable under `SQLite`
* performance: PostgreSQL has been proven superior, especially in query-performance

Use a WSGI Server
.................

Although GHC can be run from the commandline using the Flask internal WSGI web-server, this
is a fragile and possibly insecure option in production use (as also the Flask manual states).
Best is to use a WSGI-server as stated in the `Flask deployment options <http://flask.pocoo.org/docs/1.0/deploying/#deployment>`_.

See for example the `GHC Docker run.sh <https://github.com/geopython/GeoHealthCheck/blob/master/docker/scripts/run-web.sh>`_
script to run the GHC Webapp with `gunicorn` and the `GHC Runner run-runner.sh <https://github.com/geopython/GeoHealthCheck/blob/master/docker/scripts/run-runner.sh>`_ script
to run the scheduled healthchecks.

Use virtualenv
..............

This is a general Python-recommendation. Save yourself from classpath and library hells by using `virtualenv`! Starting with python 3.3
a `venv script <https://docs.python.org/3.3/library/venv.html>` is provided and from python 3.6 the `venv module <https://docs.python.org/3/library/venv.html>`
is included in the standard library.

Use SSL (HTTPS)
...............

As users and admin may login, running on plain http will send passwords in the clear.
These days it has become almost trivial to automatically install SSL certificates
with `Let's Encrypt <https://letsencrypt.org/>`_.
