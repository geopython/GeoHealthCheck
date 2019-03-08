.. _userguide:

User Guide
==========

This chapter provides guidance for configuring GeoHealthCheck's (GHC) actual tasks: healthchecking
API services on (OGC) URL Endpoints. It is written from the perspective of the end-user who interacts
with GHC's webapp (UI).

Terminology
-----------

The following terminology applies:

- `Resource`: basically an endpoint URL, like an OGC WMS, FTP URL, or plain old weblink.
  For OGC-Resources this is always the root-URL, **not the Capabilities-URL**. Each Resource has a Type (see below).
- `Probe`: each `Resource` is tested via one or more `Probes`, a Probe is typically a single HTTP request, like `GetCapabilities`, `GetMap` etc. Each `Resource` (Type) has a default `Probe`.
- `Check`: each `Probe` invokes one or more `Checks`, typically on the HTTP response. For example if a WMS `GetMap` returns an image object.
- `Run`: the execution and scoring of a single `Probe`. Its `Checks` determine the `Run` outcome.
- A `Run` in addition has a single verdict: `Ok` or `NotOk`.
- Each `User` owns one or more `Resources`

The main user task within the web UI is to manage (add, update, delete) a set of `Resources`.
For each `Resource` its various properties (scheduling, notifications, tags etc)
and `Probes` is managed. Subsequently, for each `Probe` its various `Checks` is managed.

Registration
------------

If the administrator of the GHC instance has enabled User Registration (**GHC_SELF_REGISTER** = `True`),
any person can register and manage `Resources` on that GHC instance. A User can only manage its own Resources.
The Admin user can always edit/manage any `Resource`.

When registering, a working email adress is required if you want to receive Resource
notifications by email and for password-recovery.

Adding Resources
----------------

Click the Add+ button for adding new resources.

The following Resource Types are available:

- Web Map Service (WMS)
- Web Feature Service (WFS)
- Web Map Tile Service (WMTS)
- Tile Map Service (TMS)
- Web Coverage Service (WCS)
- Catalogue Service (CSW)
- Web Processing Service (WPS)
- Sensor Observation Service (SOS)
- `SensorThings API <http://docs.opengeospatial.org/is/15-078r6/15-078r6.html>`_ (STA)
- Web Accessible Folder (WAF)
- Web Address (URL)
- File Transfer Protocol (FTP)
- GeoNode autodiscovery (see :ref:`geonode_notes`)


Deleting Resources
------------------

Open the Resource details by clicking its name in the Resources list.
Under the Resource title is a red Delete button.

Editing Resources
-----------------

Open the resource details by clicking its name in the resources list at the Dashboard page.
Under the resource title is a blue Edit button.

The following aspects of a `Resource` can be edited:

- Resource name
- Resource Tags
- Resource active/non-active
- Notification recipients
- Resource run schedule
- Resource Probes, select from "Probes Available"
- For each Probe: Probe parameters
- For each Probe: Probe Checks, select from "Checks Available"
- For each Check: Checks parameters

By default, when resource is created, owner's email will be added to notifications, however, resource can have arbitrary number or emails to notify.

Tagging
-------

Each Resource can be tagged with multiple tags. This provides a handy way to structure
your Resources into any kind of categories/groups, like `Production` and `Test`, common servers any other grouping.

Per-Resource Notifications
--------------------------

Notifications for each Resource can be configured in the Resource edit form:

.. figure:: _static/notifications_config.png
    :align: center
    :alt: GHC notifications configuration

    *Figure - GHC notifications configuration*


Note: if left empty, the global (email-)notification settings will apply.

Two notification channel-types are currently available:

Email
.....

Notifications can be sent to designated emails. If set in the config, GeoHealthCheck will
send notifications for all resources to emails defined in **GHC_NOTIFICATIONS_EMAIL**.
Additionally, each resource can have arbitrary list of emails (filled in **Notify emails**
field in edit-form). By default, when a Resource is created, the owner's email is added to
the list. The editing User can add any email address, even for Users not registered in
the GeoHealthCheck instance. When editing an email-list for a resource, the user will get address
suggestions based on emails added for other Resources by that User. Multiple emails should
be separated with comma (`,`) chars.

Webhook
.......

Notifications can be also sent as webhooks (through `POST` requests). A Resource can have an arbitrary
number of webhooks configured.

In the edit form, the User can configure  webhooks. Each webhook should be entered in a separate field.
Each webhook should contain at least a URL to which the `POST` request will be send. GeoHealthCheck will
send following fields with that request:

.. csv-table::
    :header: Form field,Field type,Description

    ghc.result,string,Descriptive result of failed test
    ghc.resource.url,URL,Resource's url
    ghc.resource.title,string,Resource's title
    ghc.resource.type,string,Resource's type name
    ghc.resource.view,URL,URL to resource data in GeoHealthCheck


A webhook configuration can hold additional form payload that will be sent along with GHC fields.
Syntax for configuration:

 * first line should be URL to which webhook will be sent
 * second line should be empty
 * third line (and subsequent) are used to store the custom payload, and should contain either:
   * pairs of field and value in separate lines (`field=value`)
   * a JSONified object, whose properties will be used as form fields

Configuration samples:

* URL-only:

.. code::

    http://server/webhook/endpoint


* URL with fields as field-value pairs:

.. code::

    http://server/webhook/endpoint

    foo=bar
    otherfield=someothervalue


* URL with payload as JSON:

.. code::

    http://server/webhook/endpoint

    {"foo":"bar","otherfield":"someothervalue"}

.. _geonode_notes:

GeoNode Resource Type
---------------------

*GeoNode* Resource is a virtual Resource.
It represents one GeoNode instance, but underneath
auto-discovery is applied of OWS endpoints available
in that instance. Note, that the OWS auto-discovery feature is
optional, and you should check if your GeoNode instance has this feature enabled.

When a adding *GeoNode instance* Resource, you have to enter
the URL to the GN instance's home page.
GeoHealthCheck will construct the URLs to fetch
the list of OWS endpoints and create relevant Resources (WMS, WFS, WMTS, and other OWS Resources).
It will check all endpoints provided by the GeoNode API, and will reject
those which responded with an error.

All Resources added in this way will have at least one tag,
which is constructed with the template: *GeoNode _hostname_*, where *_hostname_*
is a host name from url provided. For example, let's assume you add GeoNode
instance that is served from `demo.geonode.org`. All resources created in this way
will have *GeoNode demo.geonode.org* tag.
