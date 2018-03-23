.. _architecture:

Architecture
============

GeoHealthCheck (GHC) consists of three cooperating parts as depicted in the figure below.

.. figure:: _static/ghc-parts.jpg
    :align: center
    :alt: GHC Parts

    *Figure - GHC Parts*

The **GHC Webapp** provides the Dashboard where users configure web services
(Resources) for (scheduled) healthchecks and view the status of these checks. The **GHC Runner**
performs the actual healthchecks based on what the user configured via the GHC Webapp.
The third part is the **Database** that stores
all information like users, resources, checks, schedules, results etc.

**GHC Webapp** is run as a standard Python (Flask) webapp.
**GHC Runner** runs as a daemon process using an internal scheduler to invoke the
actual healthchecks.

**GHC Webapp** and **GHC Runner** can run as separate processes (preferred) or
both within the **GHC Webapp** process. This depends on a configuration option.
If **GHC_RUNNER_IN_WEBAPP** is set to True then the **GHC Runner** is started
within the **GHC Webapp**.

A third option is to only run the **GHC Webapp** and have the **GHC Runner** scheduled
via `cron`. This was the (only) GHC option before v0.4.0 and will be phased out
as starting with v0.4.0, per Resource scheduling was introduced and `cron` support
is highly platform-dependent (e.g. hard to use with Docker-based technologies).

Dependent on the database-type (Postgres or SQLite) the **Database** is run
within the above processes (SQLite) or as a separate process (Postgres).

Core Concepts
-------------

GeoHealthCheck is built with the following concepts in mind:

- `Resource`: a single, unique endpoint, like an OGC WMS, FTP URL, or plain old
  web link.  A GeoHealthCheck deployment typically monitors numerous `Resources`.
- `Run`: the execution and scoring of a test against a `Resource`.  A
  `Resource` may have multiple `Runs`
- Each `User` owns one or more `Resources`
- Each `Resource` is tested, "probed", via one or more `Probes`
- Each `Probe` typically runs one or more requests on a `Resource` URL
- Each `Probe` invokes one or more `Checks` to determine `Run` result
- `Probes` and `Checks` are extensible `Plugins` via respective `Probe` and `Check` classes
- One or more `Tags` can be associated with a `Resource` to support grouping
- One or more `Recipient` can be associated with a `Resource`. Each `Recipient` describes:

  * communication channel
  * target identifier

Data Model
----------

.. figure:: _static/datamodel.png
    :align: center
    :alt: GHC Data Model

    *Figure - GHC Data Model*
