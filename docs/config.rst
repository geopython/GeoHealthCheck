.. _config:

Configuration
=============

This chapter provides guidance for configuring a GeoHealthCheck instance.

Configuration Parameters
------------------------

The core configuration is in ``GeoHealthCheck/config_main.py``.
Optionally override these settings for your instance in ``instance/config_site.py``. You can specify
a configuration file in the environment settings that will override settings in both previous files.
The configuration options are:

- **SQLALCHEMY_DATABASE_URI**: the database configuration.  See the SQLAlchemy documentation for more info
- **SECRET_KEY**: secret key to set when enabling authentication. Use the output of ``paver create_secret_key`` to set this value
- **GHC_RETENTION_DAYS**: the number of days to keep Run history
- **GHC_PROBE_HTTP_TIMEOUT_SECS**: stop waiting for the first byte of a Probe response after the given number of seconds
- **GHC_MINIMAL_RUN_FREQUENCY_MINS**: minimal run frequency for Resource that can be set in web UI
- **GHC_SELF_REGISTER**: allow registrations from users on the website
- **GHC_NOTIFICATIONS**: turn on email notifications
- **GHC_NOTIFICATIONS_VERBOSITY**: receive additional email notifications than just ``Failing`` and ``Fixed`` (default ``True``)
- **GHC_WWW_LINK_EXCEPTION_CHECK**: turn on checking for OGC Exceptions in ``WWW:LINK`` Resource responses (default ``False``)
- **GHC_ADMIN_EMAIL**: email address of administrator / contact- notification emails will come from this address
- **GHC_NOTIFICATIONS_EMAIL**: list of email addresses that notifications should come to. Use a different address to **GHC_ADMIN_EMAIL** if you have trouble receiving notification emails. Also, you can set separate notification emails to specific resources. Failing resource will send notification to emails from **GHC_NOTIFICATIONS_EMAIL** value and emails configured for that specific resource altogether.
- **GHC_SITE_TITLE**: title used for installation / deployment
- **GHC_SITE_URL**: full URL of the installation / deployment
- **GHC_SMTP**:  configure SMTP settings if **GHC_NOTIFICATIONS** is enabled
- **GHC_RELIABILITY_MATRIX**: classification scheme for grading resource
- **GHC_PLUGINS**: list of Core/built-in Plugin classes or modules available on installation
- **GHC_USER_PLUGINS**: list of Plugin classes or modules provided by user (you)
- **GHC_PROBE_DEFAULTS**: Default `Probe` class to assign on "add" per Resource-type
- **GHC_METADATA_CACHE_SECS**: metadata, "Capabilities Docs", cache expiry time, default 900 secs, -1 to disable
- **GHC_REQUIRE_WEBAPP_AUTH**: require authentication (login or Basic Auth) to access GHC webapp and APIs (default: ``False``)
- **GHC_RUNNER_IN_WEBAPP**: should the GHC Runner Daemon be run in webapp (default: ``True``), more below
- **GHC_LOG_LEVEL**: logging level: 10=DEBUG 20=INFO 30=WARN(ING) 40=ERROR 50=FATAL/CRITICAL (default: 30, WARNING)
- **GHC_MAP**: default map settings

  - **url**: URL of TileLayer
  - **centre_lat**: Centre latitude for homepage map
  - **centre_long**: Centre longitude for homepage map
  - **maxzoom**: maximum zoom level
  - **subdomains**: available subdomains to help with parallel requests

Example on overriding the configuration with an environment variable: ::

    export GHC_SETTINGS=/tmp/my_GHC_settings.py
    paver run_tests

As an example: the `my_GHC_settings.py` file can contain a single line to define a test database: ::

    SQLALCHEMY_DATABASE_URI='sqlite:////tmp/GHCtest.db'

**NOTE**: do not forget to reset the environment variable afterwards.

Email Configuration
-------------------

A working email-configuration is required for notifications and password recovery.
This can sometimes be tricky, below is a working configuration for the GMail account
`my_gmail_name@gmail.com`. ::

	GHC_SMTP = {
	    'server': 'smtp.gmail.com',
	    'port': 587,
	    'tls': True,
	    'ssl': False,
	    'username': 'my_gmail_name@gmail.com',
	    'password': '<my gmail password>'
	}

In your Google Account settings for that GMail address you should turn on *"Allow less secure apps"*
as `explained here <https://support.google.com/accounts/answer/6010255>`_.

.. _admin_running:

Healthcheck Scheduling
----------------------

Healthchecks (Runs) for each Resource can be scheduled via `cron` or
(starting with v0.5.0) by running the **GHC Runner** app standalone (as daemon)
or within the **GHC Webapp**.

Scheduling via Cron
...................

**Applies only to pre-0.5.0 versions.**

Edit the file ``jobs.cron`` so that the paths reflect the path to the virtualenv.
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
Later versions may phase out cron-scheduling completely.

The **GHC Runner** can be run via the command `paver runner_daemon` or can run internally within
the **GHC Webapp** by setting the config variable **GHC_RUNNER_IN_WEBAPP** to `True` (the default).
NB it is still possible to run GHC as in the pre-v0.5.0 mode using cron-jobs: just run the
**GHC Webapp** with **GHC_RUNNER_IN_WEBAPP** set to `False` and have your cron-jobs scheduled.

In summary there are three options to run GHC and its healthchecks:

* run **GHC Runner** within the **GHC Webapp**: set **GHC_RUNNER_IN_WEBAPP** to `True` and run only the GHC webapp
* (recommended): run **GHC Webapp** and **GHC Runner** separately (set **GHC_RUNNER_IN_WEBAPP** to `False`)
* (deprecated): run **GHC Webapp** with **GHC_RUNNER_IN_WEBAPP** set to `False` and schedule healthchecks via external cron-jobs


Language Translations
---------------------

GHC supports multiple languages by using [Babel](http://babel.pocoo.org) with [Flask-Babel](https://pythonhosted.org/Flask-Babel/).

*"Babel is an integrated collection of utilities that assist in internationalizing*
*and localizing Python applications, with an emphasis on web-based applications."*

Enabling/Disabling a Language
.............................

Open the file `GeoHealthCheck/app.py` and look for the language switcher (e.g. 'en','fr') and remove or add the desired languages.
In case of a new language, a new translation file (called a `*.po`) has to be added as follows:

* make a copy of one of the folders in `GeoHealthCheck/translations/`;
* rename the folder to the desired language (e.g. `'de'` for German) using the language ISO codes
* edit the file `<your_lang>/LC_MESSAGES/messages.po`, adding your translations to the `msgstr`

Don't forget the change the specified language in the `messages.po` file as well.
For example the `messages.po` file for the German case has an English  `msgid`  string,
which needs to be translated in `msgstr'` as seen below.  ::

    #: GeoHealthCheck/app.py:394
    msgid "This site is not configured for self-registration"
    msgstr "Diese Webseite unterstützt keine Selbstregistrierung"

Compiling Language Files
........................

At runtime compiled versions, `*.mo` files, of the language-files are used.
Easiest to compile is via: `paver compile_translations` in the project root dir.
This basically calls ``pybabel compile` with the proper options.
Now you can e.g. test your new translations by starting GHC.

Updating Language Files
.......................

Once a language-file (`.po`) is present, it will need updating as development progresses.
In order to know what to update (which strings are untranslated) it best to first update the `messages.po` file with
all language strings, their location(s) within project files and whether the translation is missing.
Missing translations will have `msgstr ""` like in this excerpt: ::

	#: GeoHealthCheck/notifications.py:245 GeoHealthCheck/notifications.py:247
	msgid "Passing"
	msgstr "Jetzt geht's"

	#: GeoHealthCheck/plugins/probe/ghcreport.py:115
	msgid "Status summary"
	msgstr ""

Next all empty `msgstr`s can be filled.

Updating is easiest using the command `paver update_translations` within the root dir of the project.
This will basically call `pybabel extract` followed by `pybabel update` with the proper parameters.

Customizing the Score Matrix
----------------------------

GeoHealthCheck uses a simple matrix to provide an indication of overall health
and / or reliability of a resource.  This matrix drives the CSS which displays
a given resource's state with a colour.  The default matrix is defined as
follows:

.. csv-table::
  :header: low,high,score/colour

  0,49,red
  50,79,orange
  80,100,green

To adjust this matrix, edit **GHC_RELIABILITY_MATRIX** in
``instance/config_site.py``.

Securing GHC Webapp
-------------------

In some cases it is required that only logged-in (authenticated) users like the ``admin`` user can
access the entire GHC webapp and its APIs. In that case the config setting **GHC_REQUIRE_WEBAPP_AUTH**
should be set to ``True``. (version 0.7+). Non-authenticated users will be presented with
the login screen. Initially only the ``admin`` user will be able to login, but it is possible to register
and allow additional users by registering these within the ``admin`` login session.
Note that password reset is still enabled. For remote REST API calls standard HTTP Basic
Authentication (via the HTTP `Authentication` request header) can be used.
