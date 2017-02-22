.. _plugins:

Plugins
=======

GHC can be extended for Resource-specific healthchecks via Plugins.
GHC already comes with a set of standard plugins that may suffice
most installations. However, there is no limit to detailed healthchecks
one may want to perform. Hence developers can extend or even replace
the GHC standard Plugins with custom implementations.

Two extension points exist: `ProbeRunners` and `Checkers`.

*TODO: extend once Plugin implementation stabilizes...*

Configuration
-------------

Plugins available to a GHC installation are configured via `site_admin.py`.

- **GHC_PLUGINS**: list of Plugin classes or modules available on installation


Plugin API Docs
---------------

For GHC extension via Plugins the following classes apply.
Most Plugins have `@Parameter` decorators. These are variables that
should be filled in by the user unless a fixed `value` applies.

Plugins - Base Classes
......................

These are the base classes for GHC Plugins. Developers will
mainly extend `ProbeRunner` and `Checker`.

.. automodule:: GeoHealthCheck.plugin
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.proberunner
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.checker
   :members:
   :show-inheritance:

Plugins - Proberunners
......................

`Proberunners` apply to a single `Resource` instance. They are responsible for running
requests against the Resource URL endpoint. Most `Proberunners` are implemented mainly
via configuring class variables and `@Parameters` and `@Checks`, but one is free
to override any of the `Proberunner` baseclass methods.

.. automodule:: GeoHealthCheck.plugins.probe.http
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.owsgetcaps
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.tms
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.wfsgetfeature
   :members:
   :show-inheritance:

Plugins - Checkers
..................

`Checkers` apply to a single `ProbeRunner` instance. They are responsible for checking
request results from their `ProbeRunner`.

.. automodule:: GeoHealthCheck.plugins.check.checkers
   :members:
   :show-inheritance:


