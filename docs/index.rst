GeoHealthCheck
==============

Overview
--------

GeoHealthCheck is a Python application to support monitoring OGC services uptime,
availability and Quality of Service (QoS).

It can be used to monitor overall health of OGC services like WMS, WFS, WCS, WMTS, SOS, CSW
and more, but also standard web(-API) URLs.

Features
--------

- lightweight (Python with Flask)
- easy setup
- support for numerous OGC resources
- flexible and customizable: look and feel, scoring matrix
- user management
- database agnostic: any SQLAlchemy supported backend
- database upgrades: using Alembic with Flask-Migrate
- extensible healthchecks via Plugins

Links
-----

- website: http://geohealthcheck.org
- GitHub: https://github.com/geopython/geohealthcheck
- Demo: http://demo.geohealthcheck.org (official demo)
- DevDemo: http://dev.geohealthcheck.org (latest development demo)
- Presentation: http://geohealthcheck.org/presentation
- Gitter Chat: https://gitter.im/geopython/GeoHealthCheck

This is document version |release| generated on |today|.

Contents:

.. toctree::
   :maxdepth: 2

   install.rst
   config.rst
   admin.rst
   architecture.rst
   plugins.rst
   license.rst
   contact.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
