.. _admin:

Adminstration
=============


Database
--------

For database administration the following commands are available.

NB, although SQLite works fine for most installations it is recommended
for performance and reliability to use PostgreSQL.

create db
.........

To create the database execute the following:

Open a command line, (if needed activate your virtualenv), and do ::

    python GeoHealthCheck/models.py create

drop db
.......

To delete the database execute the following, however you will loose all your information. So please ensure backup if needed:

Open a command line, (if needed activate your virtualenv), and do ::

    python GeoHealthCheck/models.py drop

Note: you need to create a Database again before you can start GHC again.

load data
.........

To load a JSON data file, do (WARN: deletes existing data!) ::

    python GeoHealthCheck/models.py load <datafile.json> [y/n]

Hint: see `tests/data` for example JSON data files.

export data
...........

Exporting database-data to a .json file with or without Runs is still to be done.

Exporting Resource and Run data from a running GHC instance can be effected via
a REST API, for example:

* all Resources: http://demo.geohealthcheck.org/json  (or `as CSV <http://demo.geohealthcheck.org/csv>`_)
* one Resource: http://demo.geohealthcheck.org/resource/1/json (or `CSV <http://demo.geohealthcheck.org/resource/1/csv>`_)
* all history (Runs) of one Resource: http://demo.geohealthcheck.org/resource/1/history/json (or `in csv <http://demo.geohealthcheck.org/resource/1/history/csv>`_)

NB for detailed reporting data only JSON is supported.

User Management
---------------

On setup a single `admin` user is created interactively.

Via the **GHC_SELF_REGISTER** config setting, you allow/disallow registrations from users on the website.

Adding Resources
----------------

When being logged in, click the Add+ button for adding new resources.

The folowing resource types are available:

- File Transfer Protocol (FTP)
- Web Map Service (WMS)
- Web Address (URL)
- Catalogue Service (CSW)
- Web Map Tile Service (WMTS)
- Web Processing Service (WPS)
- Web Coverage Service (WCS)
- Web Feature Service (WFS)
- Tile Map Service (TMS)
- Web Accessible Folder (WAF)
- Sensor Observation Service (SOS)
- `SensorThings API <http://docs.opengeospatial.org/is/15-078r6/15-078r6.html>`_ (STA)
- GeoNode autodiscovery


Deleting Resources
------------------

Open the resource details by clicking its name in the resources list at the Dashboard page.
Under the resource title is a red Delete button.

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

Running Healthchecks
--------------------

Healthchecks (Runs) for each Resource can be scheduled via `cron` or
(since v0.4.0) by running the **GHC Runner** app standalone (as daemon)
or within the **GHC Webapp**.

Scheduling via Cron
...................

Edit the file ``jobs.cron`` that the paths reflect the path to the virtualenv.
Set the first argument to the desired monitoring time step. If finished editing,
copy the command line calls e.g. ``/YOURvirtualenv/bin_or_SCRIPTSonwindows/python /path/to/GeoHealthCheck/GeoHealthCheck/healthcheck.py run``
to the commandline to test if they work sucessfully.
On Windows - do not forget to include the ''.exe.'' file extension to the python executable.
For documentation how to create cron jobs see your operating system: on \*NIX systems e.g.  ``crontab -e`` and on
windows e.g. the `nssm <https://nssm.cc/>`_.

NB the limitation of cron is that the per `Resource` schedule cannot be applied as
the cron job will run healthchecks on all `Resources`.

GHC Runner as Daemon
....................

In this mode GHC applies internal scheduling for each individual `Resource`.
This is the preferred mode as each `Resource` can have its own schedule (configurable
via Dashboard) and `cron` has dependencies on local environment.
Later versions may phase out cron-scheduling.
The **GHC Runner** can be run via the command `paver runner_daemon` or internally within
the **GHC Webapp** by setting the config variable **GHC_RUNNER_IN_WEBAPP** to True.


Build Documentation
-------------------

Open a command line, (if needed activate your virtualenv) and move into the directory  ``GeoHealthCheck/doc/``.
In there, type ''make html'' plus ENTER and the documentation should be build locally.

GeoNode Resource Type Notes
---------------------------

*GeoNode* Resource is a virtual resource.
It represents one GeoNode instance, but underneath
auto-discovery is applied of OWS endpoints available
in that instance. Note, that OWS auto-discovery feature is
optional, and you should check if your GeoNode instance has this feature enabled.

When adding *GeoNode instance* Resource, you have to enter
the url to the GN instance's home page.
GeoHealthCheck will construct the urls to target
OWS endpoints listing and create relevant Resources (WMS, WFS, WMTS, OWC Resources).
It will check all endpoints provided by the GeoNode API, and will reject
those which responded with an error.

All resources added in this way will have at least one tag,
which is constructed with template: *GeoNode _hostname_*, where *_hostname_*
is a host name from url provided. For example, let's assume you add GeoNode
instance that is served from `demo.geonode.org`. All resources created in this way
will have *GeoNode demo.geonode.org* tag.
