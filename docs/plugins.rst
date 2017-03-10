.. _plugins:

Plugins
=======

GHC can be extended for Resource-specific healthchecks via Plugins.
GHC already comes with a set of standard plugins that may suffice
most installations. However, there is no limit to detailed healthchecks
one may want to perform. Hence developers can extend or even replace
the GHC standard Plugins with custom implementations.

Two extension points exist: the `Probe` and `Check` classes.

*TODO: extend once Plugin implementation stabilizes...*

Configuration
-------------

Plugins available to a GHC installation are configured via `site_admin.py`.

- **GHC_PLUGINS**: `list` of Plugin classes and/or modules available on installation


Plugin API Docs
---------------

For GHC extension via Plugins the following classes apply.

Most Plugins have `PARAM_DEFS` parameter definitions. These are variables that
should be filled in by the user in the GUI unless a fixed `value` applies.

Plugins - Base Classes
......................

These are the base classes for GHC Plugins. Developers will
mainly extend `Probe` and `Check`.

.. automodule:: GeoHealthCheck.plugin
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.probe
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.check
   :members:
   :show-inheritance:

Plugins - Probes
................

`Probes` apply to a single `Resource` instance. They are responsible for running
requests against the Resource URL endpoint. Most `Probes` are implemented mainly
via configuring class variables in particular `PARAM_DEFS` and `CHECKS_AVAIL`, but one is free
to override any of the `Probe` baseclass methods.

.. automodule:: GeoHealthCheck.plugins.probe.http
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.owsgetcaps
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.wms
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.wmsdrilldown
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.tms
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.wfs
   :members:
   :show-inheritance:

Plugins - Checks
................

`Checks` apply to a single `Probe` instance. They are responsible for checking
request results from their `Probe`.

.. automodule:: GeoHealthCheck.plugins.check.checks
   :members:
   :show-inheritance:


