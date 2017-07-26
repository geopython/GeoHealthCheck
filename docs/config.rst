.. _config:

Configuration
=============

Core configuration is set by GeoHealthCheck in ``GeoHealthCheck/config_main.py``.
You can override these settings in ``instance/config_site.py``:

- **SQLALCHEMY_DATABASE_URI**: the database configuration.  See the
  SQLAlchemy documentation for more info
- **SECRET_KEY**: secret key to set when enabling authentication.  Use
  the output of ``paver create_secret_key`` to set this value
- **GHC_RETENTION_DAYS**: the number of days to keep run history
- **GHC_RUN_FREQUENCY**: cron keyword used to indicate frequency of runs
  (i.e. ``hourly``, ``daily``, ``monthly``)
- **GHC_SELF_REGISTER**: allow registrations from users on the website
- **GHC_NOTIFICATIONS**: turn on email notifications
- **GHC_NOTIFICATIONS_VERBOSITY**: receive additional email notifications than just ``Failing`` and ``Fixed`` (default ``True``)
- **GHC_WWW_LINK_EXCEPTION_CHECK**: turn on checking for OGC Exceptions in ``WWW:LINK`` Resource responses (default ``False``)
- **GHC_ADMIN_EMAIL**: email address of administrator / contact- notification emails will come from this address
- **GHC_NOTIFICATIONS_EMAIL**: list of email addresses that notifications should come to. Use a different address to **GHC_ADMIN_EMAIL** if you have trouble receiving notification emails
- **GHC_SITE_TITLE**: title used for installation / deployment
- **GHC_SITE_URL**: url of the installation / deployment
- **GHC_SMTP**:  configure SMTP settings if **GHC_NOTIFICATIONS** is enabled
- **GHC_RELIABILITY_MATRIX**: classification scheme for grading resource
- **GHC_PLUGINS**: list of Core/built-in Plugin classes or modules available on installation
- **GHC_USER_PLUGINS**: list of Plugin classes or modules provided by user (you)
- **GHC_PROBE_DEFAULTS**: Default `Probe` class to assign on "add" per Resource-type
- **GHC_METADATA_CACHE_SECS**: metadata, "Capabilities Docs", cache expiry time, default 900 secs, -1 to disable
- **GHC_MAP**: default map settings

  - **url**: URL of TileLayer
  - **centre_lat**: Centre latitude for homepage map
  - **centre_long**: Centre longitude for homepage map
  - **maxzoom**: maximum zoom level
  - **subdomains**: available subdomains to help with parallel requests


Enabling or disabling languages
-------------------------------

Open the file ``GeoHealthCheck/app.py`` and look for the language switcher (e.g. 'en','fr') and remove or add the desired languages.
In case a new language (e.g. this needs a new translation file called ``*.po``)  is to be added,
make a copy of  one of the folders in ``GeoHealthCheck/translations/``; rename the folder to the desired language (e.g. 'de' for german);
start editing the file in ``LC_MESSAGES/messages.po`` and add your translations to the ''msgstr''.
Don't forget the change the specified language in the messages.po file as well.
For example the ``messages.po`` file for the german case has an english  ''msgid''  string,
which needs to be translated in ''msgstr'' as seen below.  ::

    -#: GeoHealthCheck/app.py:394
    -msgid "This site is not configured for self-registration"
    -msgstr "Diese Webseite unterstützt keine Selbstregistrierung"


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

