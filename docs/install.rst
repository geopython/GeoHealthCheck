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

These dependencies are automatically installed (see below). A command line interface is provided
 with `click`. ``Cron`` was used for scheduling the actual healthchecks before v0.5.0.

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

  # install
  pip install .

  # setup app
  geohc create-instance

  # create secret key to use for auth
  geohc create-secret-key

  # almost there!  Customize config
  vi instance/config_site.py
  # edit:
  # - SQLALCHEMY_DATABASE_URI
  # - SECRET_KEY  # from geohc create-secret-key
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

  # init database
  geohc db-create

  # create an (admin) user account
  geohc db-adduser -u my_user_name -p my_pass -e e@mail.com -r admin

  # start web-app
  geohc serve

  # when you are done, you can exit the virtualenv
  deactivate

NB GHC supports internal scheduling, no cronjobs required.

Developing
..........
If you plan to develop with the GeoHealthCheck code base, you might want to install with the
*editable* option specified: `pip install -e`. This gives you access to the command line interface,
and you can still edit and run the code.

.. _upgrade:

Upgrade
-------

An existing GHC database installation can be upgraded with:

.. code-block:: bash

  # In the top directory (e.g. the topdir cloned from github)
  geohc db-upgrade

  # Notice any output, in particular errors

Notes:

* **Always backup your database first!!**
* make sure Flask-Migrate is installed (see requirements.txt), else:  `pip install Flask-Migrate==2.5.2`, but best is to run `geohc create-instance` also for other dependencies
* upgrading is "smart": you can always run `geohc db upgrade`, it has no effect when DB is already up to date
* when upgrading from earlier versions without Plugin-support:

  - adapt your `config_site.py` to Plugin settings from `config_main.py`
  - assign `Probes` and `Checks` to each `Resource` via the UI

When running with Docker see the
`Docker Readme <https://github.com/geopython/GeoHealthCheck/blob/master/docker/README.md>`_
how to run `geohc upgrade` within your Docker Container.

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

Upgrade notes v0.8.0
....................

In previous version GHC used `paver` to control the setup and administration of
the application. With this version GHC switched `click` and the cli commands
changed to `geohc`. Type `geohc --help` to get more information.


Running
-------

Start using Flask's built-in WSGI server:

.. code-block:: bash

  geohc serve  # http://localhost:8000
  geohc serve --port 8881  # http://localhost:8881
  geohc serve --host 192.168.0.105 --port 8957  # http://192.168.0.105:8957


This runs the (Flask) **GHC Webapp**, by default with the **GHC Runner** (scheduled healthchecker) internally.
See also :ref:`admin_running` for the different options running the **GHC Webapp** and **GHC Runner**. It is
recommended to run these as separate processes. For this set **GHC_RUNNER_IN_WEBAPP** to `False` in your `site_config.py`.
From the command-line run both processes, e.g. in background or different terminal sessions:

.. code-block:: bash

  # run GHC Runner, here in background
  geohc runner-daemon &

  # run GHC Webapp for http://localhost:8000
  geohc serve


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
