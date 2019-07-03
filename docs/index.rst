GeoHealthCheck
==============

Overview
--------

GeoHealthCheck (GHC) is a Python application to support monitoring OGC services uptime,
availability and Quality of Service (QoS).

GHC can be used to monitor overall health of OGC services (OWS) like WMS, WFS, WCS, WMTS, SOS, CSW
and more, plus some recent OGC APIs like SensorThings API and WFS v3 (OGC Features API).
But also standard web REST APIs and ordinary URLs can be monitored.

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
- per-resource scheduling and notifications
- per-resource HTTP-authentication like Basic, Token (optional)

Links
-----

- website: http://geohealthcheck.org
- GitHub: https://github.com/geopython/geohealthcheck
- Demo: https://demo.geohealthcheck.org (official demo, master branch)
- Presentation: http://geohealthcheck.org/presentation
- Gitter Chat: https://gitter.im/geopython/GeoHealthCheck

This document applies to GHC version |release| and was generated on |today|.
The latest version is always available at http://docs.geohealthcheck.org.

Contents:

.. toctree::
   :numbered:
   :maxdepth: 2

   install.rst
   config.rst
   admin.rst
   userguide.rst
   architecture.rst
   plugins.rst
   license.rst
   contact.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
