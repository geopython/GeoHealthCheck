.. _plugins:

Plugins
=======

GHC can be extended for Resource-specific healthchecks via Plugins.
GHC already comes with a set of standard plugins that may suffice
most installations. However, there is no limit to detailed healthchecks
one may want to perform. Hence developers can extend or even replace
the GHC standard Plugins with custom implementations.

Two Plugin types exist that can be extended: the `Probe` and `Check` class.
In v0.7.0 also plugins for Resource Authentication, `ResourceAuth`, were added
and in v0.9.0 the geocoder plugin was introduced.

Concepts
--------

GHC versions after May 1, 2017 perform healthchecks exclusively via Plugins
(see :ref:`upgrade` how to upgrade from older versions). The basic concept
is simple: each `Resource` (typically an OWS endpoint) has one or more `Probes`. During a
GHC run (via `cron` or manually), GHC sequentually invokes the `Probes` for each `Resource`
to determine the health (QoS) of the `Resource`.

A `Probe` typically
implements a single request like a `WMS GetMap`. A `Probe` contains and applies one or more `Checks` (the other Plugin class).
A `Check` implements typically a single check on the HTTP Response object of its parent `Probe`, for example
if the HTTP response has no errors or if a `WMS GetMap` actually returns an image (content-type check).
Each `Check` will supply a `CheckResult` to its parent `Probe`. The list of `CheckResults` will then ultimately
determine the `ProbeResult`. The `Probe` will in turn supply the `ProbeResult` to its parent `ResourceResult`.
The GHC healthchecker will then determine the final outcome of the `Run` (fail/success) for the `Resource`, adding
the list of Probe/CheckResults to the historic Run-data in the DB. This data can later be used for reporting and
determining which `Check(s)` were failing.

So in summary: a `Resource` has one or more `Probes`, each `Probe` one or more `Checks`. On a GHC run
these together provide a `Result`.

Probes and Checks available to the GHC instance are configured in `config_site.py`, the GHC instance config file.
Also configured there is the default `Probe` class to assign to a Resource-type when it is added.
Assignment and configuration/parameterization of `Probes` and `Checks` is via de UI on the
Resource-edit page and stored in the database (tables: `probe_vars` and `check_vars`). That way
the GHC healthcheck runner can read (from the DB) the list of Probes/Checks and their config for
each Resource.

Implementation
--------------

`Probes` and `Checks` plugins are implemented as Python classes derived from
:class:`GeoHealthCheck.probe.Probe` and :class:`GeoHealthCheck.check.Check` respectively.
These classes inherit from the GHC abstract base class :class:`GeoHealthCheck.plugin.Plugin`.
This class mainly provides default attributes (in capitals) and introspection methods needed for
UI configuration. *Class-attributes* (in capitals) are the most important concept of GHC Plugins in general.
These provide metadata for various GHC functions (internal, UI etc). General class-attributes that
Plugin authors should provide for derived `Probes` or `Checks` are:

* `AUTHOR`:  Plugin author or team.
* `NAME`:     Short name of Plugin.
* `DESCRIPTION`: Longer description of Plugin.
* `PARAM_DEFS`: Plugin Parameter definitions (see next)

`PARAM_DEFS`, a Python `dict` defines the parameter definitions for the `Probe` or `Check` that
a user can configure via the UI.
Each parameter (name) is itself a `dict` entry key that with the following key/value pairs:

* `type`: the parameter type, value: 'string', 'stringlist' (comma-separated strings) or 'bbox' (lowerX, lowerY, upperX, upperY),
* `description`: description of the parameter,
* `default`: parameter default value,
* `required`: is parameter required?,
* `range`: range of possible parameter values (array of strings), results in UI dropdown selector

A `Probe` should supply these additional class-attributes:

* `RESOURCE_TYPE` : GHC Resource type this Probe applies to, e.g. `OGC:WMS`, `*:*` (any Resource Type), see `enums.py` for range
* `REQUEST_METHOD` : HTTP request method capitalized, 'GET' (default) or 'POST'.
* `REQUEST_HEADERS` : `dict` of optional HTTP request headers
* `REQUEST_TEMPLATE`: template in standard Python `str.format(*args)` to be substituted with actual parameters from `PARAM_DEFS`
* `CHECKS_AVAIL` : available Check (classes) for this Probe.

Note: `CHECKS_AVAIL` denotes all possible `Checks` that can be assigned, by default or via UI,
to an instance of this `Probe`.

A `Check` has no additional class-attributes.

In many cases writing a `Probe` is a matter of just defining the above class-attributes.
The GHC healthchecker :meth:`GeoHealthCheck.healthcheck.run_test_resource` will call lifecycle
methods of the :class:`GeoHealthCheck.probe.Probe`
base class, using the class-attributes and actualized parameters (stored in `probe_vars` table)
as defined in `PARAM_DEFS` plus a list of the actual and parameterized Checks (stored in `check_vars` table) for its Probe instance.

More advanced
`Probes` can override base-class methods of `Probe` in particular :meth:`GeoHealthCheck.probe.Probe.perform_request`.
In that case the Probe-author should add one or more :class:`GeoHealthCheck.result.Result` objects
to `self.result` via `self.result.add_result(result)`

Writing a `Check` class requires providing the Plugin class-attributes (see above) including
optional `PARAM_DEFS`. The actual check is implemented by overriding the `Check` base class
method :meth:`GeoHealthCheck.check.Check.perform`, setting the check-result via
:meth:`GeoHealthCheck.check.Check.set_result`.

Finally your Probes and Checks need to be made available to your GHC instance
via `config_site.py` and need to be found on the Python-PATH of your app.

The above may seem daunting at first. Examples below will hopefully make things clear
as writing new `Probes` and `Checks` may sometimes be a matter of minutes!

*TODO: may need VERSION variable class-attr to support upgrades*

Examples
--------

GHC includes Probes and Checks that on first setup are made available in
`config_site.py`. By studying the the GHC standard Probes and Checks under the subdir
`GeoHealthCheck/plugins`, Plugin-authors may get a feel how implementation can be effected.

There are broadly two ways to write a `Probe`:

* using a `REQUEST_*` class-attributes, i.e. letting GHC do the Probe's HTTP requests and checks
* overriding :meth:`GeoHealthCheck.probe.Probe.perform_request`: making your own requests

An example for each is provided, including the `Checks` used.

The simplest Probe is one that does:

* an HTTP GET on a `Resource` URL
* checks if the HTTP Response is not errored, i.e. a 404 or 500 status
* optionally checks if the HTTP Response (not) contains expected strings

Below is the implementation of the class :class:`GeoHealthCheck.plugins.probe.http.HttpGet`:

.. literalinclude:: ../GeoHealthCheck/plugins/probe/http.py
   :language: python
   :lines: 1-23
   :linenos:   

Yes, this is the entire implementation of :class:`GeoHealthCheck.plugins.probe.http.HttpGet`!
Only class-attributes are needed: 

* standard Plugin attributes: `AUTHOR` ('GHC Team' by default) `NAME`, `DESCRIPTION`
* `RESOURCE_TYPE = '*:*'` denotes that any Resource may use this Probe (UI lists this Probe under "Probes Available" for Resource)
* `REQUEST_METHOD = 'GET'` : GHC should use the HTTP GET request method
* `CHECKS_AVAIL` : all Check classes that can be applied to this Probe (UI lists these under "Checks Available" for Probe)

By setting: ::

   'GeoHealthCheck.plugins.check.checks.HttpStatusNoError': {
      'default': True
   },

that Check is automatically assigned to this Probe when created. The other Checks may be added and configured via
the UI.

Next look at the Checks, the class :class:`GeoHealthCheck.plugins.check.checks.HttpStatusNoError`:

.. literalinclude:: ../GeoHealthCheck/plugins/check/checks.py
   :language: python
   :lines: 1-34
   :linenos:

Also this class is quite simple: providing class-attributes `NAME`, `DESCRIPTION` and implementing
the base-class method :meth:`GeoHealthCheck.check.Check.perform`. Via `self.probe` a Check always
has a reference to its parent Probe instance and the HTTP Response object via `self.probe.response`.
The check itself is a test if the HTTP status code is in the 400 or 500-range. The `CheckResult`
is implicitly created by setting: `self.set_result(False, 'HTTP Error status=%d' % status)` in case
of errors. `self.set_result()` only needs to be called when a Check fails. By default the Result is
succes (`True`).

According to this pattern more advanced Probes are implemented for `OWS GetCapabilities`, the most
basic test for OWS-es like WMS and WFS. Below the implementation
of the class :class:`GeoHealthCheck.plugins.probe.owsgetcaps.OwsGetCaps` and its derived classes
for specific OWS-es:

.. literalinclude:: ../GeoHealthCheck/plugins/probe/owsgetcaps.py
   :language: python
   :lines: 1-108
   :linenos:

More elaborate but still only class-attributes are used! Compared to
:class:`GeoHealthCheck.plugins.probe.http.HttpGet`, two additional class-attributes are used
in :class:`GeoHealthCheck.plugins.probe.owsgetcaps.OwsGetCaps` :

* `REQUEST_TEMPLATE ='?SERVICE={service}&VERSION={version}&REQUEST=GetCapabilities'`
* `PARAM_DEFS` for the `REQUEST_TEMPLATE`

GHC will recognize a `REQUEST_TEMPLATE` (for GET or POST) and use  `PARAM_DEFS` to substitute
configured or default values, here defined in subclasses. This string is then appended
to the Resource URL.

Three `Checks` are available, all included by default. Also see the construct: ::

   'GeoHealthCheck.plugins.check.checks.ContainsStrings': {
      'set_params': {
          'strings': {
              'name': 'Contains Title Element',
              'value': ['Title>']
          }
      },
      'default': True
   },

This not only assigns this Check automatically on creation, but also provides it
with parameters, in this case a `Capabilities` response document should always
contain a `<Title>` XML element. The class
:class:`GeoHealthCheck.plugins.check.checks.ContainsStrings` checks if a response doc contains
all of a list (array) of configured strings. So the full checklist on the response doc is:

* is it XML-parsable: :class:`GeoHealthCheck.plugins.check.checks.XmlParse`
* does not contain an Exception: :class:`GeoHealthCheck.plugins.check.checks.NotContainsOwsException`
* does it have a `<Title>` element: :class:`GeoHealthCheck.plugins.check.checks.ContainsStrings`

These Checks are performed in that order. If any fails, the Probe Run is in error.

We can now look at classes derived from :class:`GeoHealthCheck.plugins.probe.owsgetcaps.OwsGetCaps`, in particular
:class:`GeoHealthCheck.plugins.probe.owsgetcaps.WmsGetCaps` and :class:`GeoHealthCheck.plugins.probe.owsgetcaps.WfsGetCaps`.
These only need to set their `RESOURCE_TYPE` e.g. `OGC:WMS` and override/merge `PARAM_DEFS`. For example for WMS: ::

   PARAM_DEFS = Plugin.merge(OwsGetCaps.PARAM_DEFS, {

     'service': {
         'value': 'WMS'
     },
     'version': {
         'default': '1.1.1',
         'range': ['1.1.1', '1.3.0']
     }
   })

This sets a fixed `value` for `service`, later becoming `service=WMS` in the URL request string.
For `version` it sets both a `range` of values a user can choose from, plus a default value `1.1.1`.
`Plugin.merge` needs to be used to merge-in new values. Alternatively `PARAM_DEFS` can be completely
redefined, but in this case we only need to make per-OWS specific settings.

Also new in this example is parameterization of Checks for the class
:class:`GeoHealthCheck.plugins.check.checks.ContainsStrings`. This is a generic
HTTP response checker for a list of strings that each need to be present in the
response. Alternatively :class:`GeoHealthCheck.plugins.check.checks.NotContainsStrings` has
the reverse test. Both are extremely useful and for example available to our
first example :class:`GeoHealthCheck.plugins.probe.http.HttpGet`.
The concept of `PARAM_DEFS` is the same for Probes and Checks.

In fact a Probe for any REST API could be defined in the above matter. For example, later in the project
a Probe was added for the `SensorThings API <http://docs.opengeospatial.org/is/15-078r6/15-078r6.html>`_ (STA),
a recent OGC-standard for managing Sensor data via a JSON REST API.  See the listing below:

.. literalinclude:: ../GeoHealthCheck/plugins/probe/sta.py
   :language: python
   :linenos:


Up to now all Probes were defined using and overriding class-attributes. Next is
a more elaborate example where the Probe overrides the Probe baseclass method
:meth:`GeoHealthCheck.probe.Probe.perform_request`.  The example is
more of a showcase: :class:`GeoHealthCheck.plugins.probe.wmsdrilldown.WmsDrilldown`
literally drills-down through WMS-entities: starting with the
`GetCapabilities` doc it fetches the list of  `Layers` and does
a `GetMap` on random layers etc. It uses `OWSLib.WebMapService`.

We show the first 70 lines here.

.. literalinclude:: ../GeoHealthCheck/plugins/probe/wmsdrilldown.py
   :language: python
   :lines: 1-70
   :linenos:

This shows that any kind of simple or elaborate healthchecks can be implemented using
single or multiple HTTP requests. As long as Result objects are set via
`self.result.add_result(result)`. It is optional to also define `Checks` in this case.
In the example :class:`GeoHealthCheck.plugins.probe.wmsdrilldown.WmsDrilldown` example no
Checks are used.

One can imagine custom Probes for many use-cases:

- drill-downs for OWS-es
- checking both the service and its metadata (CSW links in Capabilities doc e.g.)
- gaps in timeseries data (SOS, STA)
- even checking resources like a remote GHC itself!

Writing custom Probes is only limited by your imagination!


Configuration
-------------

Plugins available to a GHC installation are configured via `config_main.py` and overridden in `config_site.py`.
By default all built-in Plugins are available.

- **GHC_PLUGINS**: `list` of built-in/core Plugin classes and/or modules available on installation
- **GHC_PROBE_DEFAULTS**: Default `Probe` class to assign on "add" per Resource-type
- **GHC_USER_PLUGINS**: `list` of your Plugin classes and/or modules available on installation

To add your Plugins, you need to configure **GHC_USER_PLUGINS**. In most cases you don't need to bother
with **GHC_PLUGINS** and **GHC_PROBE_DEFAULTS**.

See an example for both below from `config_main.py` for **GHC_PLUGINS** and **GHC_PROBE_DEFAULTS**: ::

   GHC_PLUGINS = [
       # Probes
       'GeoHealthCheck.plugins.probe.owsgetcaps',
       'GeoHealthCheck.plugins.probe.wms',
       'GeoHealthCheck.plugins.probe.wfs.WfsGetFeatureBbox',
       'GeoHealthCheck.plugins.probe.tms',
       'GeoHealthCheck.plugins.probe.http',
       'GeoHealthCheck.plugins.probe.sta',
       'GeoHealthCheck.plugins.probe.wmsdrilldown',
       'GeoHealthCheck.plugins.probe.ogcfeat',

       # Checks
       'GeoHealthCheck.plugins.check.checks',
   ]

   # Default Probe to assign on "add" per Resource-type
   GHC_PROBE_DEFAULTS = {
       'OGC:WMS': {
           'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WmsGetCaps'
       },
       'OGC:WMTS': {
           'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WmtsGetCaps'
       },
       'OSGeo:TMS': {
           'probe_class': 'GeoHealthCheck.plugins.probe.tms.TmsCaps'
       },
       'OGC:WFS': {
           'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WfsGetCaps'
       },
       'OGC:WCS': {
           'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WcsGetCaps'
       },
       'OGC:WPS': {
           'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.WpsGetCaps'
       },
       'OGC:CSW': {
           'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.CswGetCaps'
       },
       'OGC:SOS': {
           'probe_class': 'GeoHealthCheck.plugins.probe.owsgetcaps.SosGetCaps'
       },
       'OGC:STA': {
           'probe_class': 'GeoHealthCheck.plugins.probe.sta.StaCaps'
       },
       'OGCFeat': {
           'probe_class': 'GeoHealthCheck.plugins.probe.ogcfeat.OGCFeatDrilldown'
       },
       'ESRI': {
           'probe_class': 'GeoHealthCheck.plugins.probe.esri.ESRIDrilldown'
       },
       'urn:geoss:waf': {
           'probe_class': 'GeoHealthCheck.plugins.probe.http.HttpGet'
       },
       'WWW:LINK': {
           'probe_class': 'GeoHealthCheck.plugins.probe.http.HttpGet'
       },
       'FTP': {
           'probe_class': None
       }
   }

To add your User Plugins these steps are needed:

- place your Plugin in any directory
- specify your Plugin in `config_site.py` in **GHC_USER_PLUGINS** var
- your Plugin module needs to be available in the `PYTHONPATH` of the GHC app

Let's say your Plugin is in file `/plugins/ext/myplugin.py`. Example `config_site.py` ::

   GHC_USER_PLUGINS='ext.myplugin'

Then you need to add the path `/plugins` to the `PYTHONPATH` such that your Plugin is found.

User Plugins via Docker
-----------------------

The easiest way to add your Plugins (and running GHC in general!) is by using
`GHC Docker <https://github.com/geopython/GeoHealthCheck/tree/master/docker/README.md>`_.
See more info in the `GHC Docker Plugins README <https://github.com/geopython/GeoHealthCheck/blob/master/docker/plugins/README.md>`_.

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

.. automodule:: GeoHealthCheck.resourceauth
   :members:
   :show-inheritance:


`Results` are helper-classes whose intances are
generated by both `Probe` and `Check` classes. They form the ultimate outcome when
running a `Probe`. A `ResourceResult` contains `ProbeResults`, the latter contains
`CheckResults`.

.. automodule:: GeoHealthCheck.result
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

.. automodule:: GeoHealthCheck.plugins.probe.wmts
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.sta
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.wfs
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.wcs
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.ogcfeat
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.mapbox
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.ogc3dtiles
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.esri
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.probe.ghcreport
   :members:
   :show-inheritance:

Plugins - Checks
................

`Checks` apply to a single `Probe` instance. They are responsible for checking
request results from their `Probe`.

.. automodule:: GeoHealthCheck.plugins.check.checks
   :members:
   :show-inheritance:

Plugins - Resource Auth
.......................

`ResourceAuth` apply to optional authentication for a `Resource` instance. They are responsible for handling
any (UI) configuration, encoding and execution of specific HTTP authentication methods for the `Resource` endpoint.

.. automodule:: GeoHealthCheck.plugins.resourceauth.resourceauths
   :members:
   :show-inheritance:

Plugins - Geocoder
..................

`Geocoder` apply to geocoder services. They are responsible for geolocating a server on a map.

.. automodule:: GeoHealthCheck.plugins.geocode.fixedlocation
   :members:
   :show-inheritance:

.. automodule:: GeoHealthCheck.plugins.geocode.webgeocoder
   :members:
   :show-inheritance:



