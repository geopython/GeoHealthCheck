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

TODO: export data to .json file with or without runs.

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


Deleting Resources
------------------

Open the resource details by clicking its name in the resources list at the Dashboard page. Under the resource title is a red Delete button.

Editing Resources
-----------------

Open the resource details by clicking its name in the resources list at the Dashboard page. Under the resource title is a blue Edit button.

The following aspects of a `Resource` can be edited:

- Resource name
- Resource Tags
- Resource Probes
- For each Probe: Probe parameters
- For each Probe: Probe Checks
- For each Check: Probe parameters (TODO)

Scheduling Runs
---------------

- Permanent Jobs

Edit the file ``jobs.cron`` that the paths reflect the path to the virtualenv.
Set the first argument to the desired monitoring time step. If finished editing,
copy the command line calls e.g. ``/YOURvirtualenv/bin_or_SCRIPTSonwindows/python /path/to/GeoHealthCheck/GeoHealthCheck/models.py run``
to the commandline to test if they work sucessfully.
On Windows - do not forget to include the ''.exe.'' file extension to the python executable.
For documentation how to create cron jobs see your operating system: on \*NIX systems e.g.  ``crontab -e`` and on
windows e.g. the `nssm <https://nssm.cc/>`_.

- interactive
  TBF

Build Documentation
-------------------

Open a command line, (if needed activate your virtualenv) and move into the directory  ``GeoHealthCheck/doc/``.
In there, type ''make html'' plus ENTER and the documentation should be build locally.




