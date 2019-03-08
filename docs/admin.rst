.. _admin:

Administration
==============

This chapter describes maintenance tasks for the administrator of a GHC instance.
There is a separate :ref:`userguide` that provides guidance to the end-user to
configure the actual Resource healthchecks.

Each of the sections below is geared at a specific administrative task area.

Database
--------

For database administration the following commands are available.

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

* all Resources: https://demo.geohealthcheck.org/json  (or `as CSV <https://demo.geohealthcheck.org/csv>`_)
* one Resource: https://demo.geohealthcheck.org/resource/1/json (or `CSV <https://demo.geohealthcheck.org/resource/1/csv>`_)
* all history (Runs) of one Resource: https://demo.geohealthcheck.org/resource/1/history/json (or `in csv <https://demo.geohealthcheck.org/resource/1/history/csv>`_)

NB for detailed reporting data only JSON is supported.

.. _admin_user_mgt:

User Management
---------------

During initial setup, a single `admin` user is created interactively.

Via the **GHC_SELF_REGISTER** config setting, you allow/disallow registrations from users on the webapp (UI).

Passwords
.........

Passwords are stored encrypted. Even the same password-string will have different "hashes".
There is no way that GHC can decrypt a stored password. This can become a challenge in cases where
a password is forgotten and somehow the email-based reset is not available nor working.
In that case, password-hashes can be created from the command-line using the Python library `passlib <https://passlib.readthedocs.io/en/stable/>`_
within an interactive Python-shell as follows: ::

	$ pip install passlib
	# or in Debian/Ubuntu: apt-get install python-passlib

	pythonfrom passlib.hash import pbkdf2_sha256
	>>>
	>>> hash = pbkdf2_sha256.hash("mynewpassword")
	>>> print hash
	$pbkdf2-sha256$29000$da51rlVKKWVsLSWEsBYCoA$2/shIdqAxGJkDq6TTeIOgQKbtYAOPSi5EA3TDij1L6Y
	>>> pbkdf2_sha256.verify("mynewpassword", hash)
	True

Or more compact within the root dir of your GHC installation: ::

	>>> from GeoHealthCheck.util import create_hash
	>>> create_hash('mynewpassword')
	'$pbkdf2-sha256$29000$8X4PAUAIAcC4V2rNea9Vqg$XnMx1SfEiBzBAMOQOOC7uxCcyzVuKaHENLj3IfXvfu0'

Or even more compact within the root dir of your GHC installation via Paver: ::

	$ paver create_hash -p mypass
	---> pavement.create_hash
	Copy/paste the entire token below for example to set password
	$pbkdf2-sha256$29000$FkJoTYnxPqc0pjQG4HxP6Q$C3SZb8jqtM7zKS1DSLcouc/CL9XMI9cL5xT6DRTOEd4

Then copy-paste the hash-string into the `password`-field of the User-record in the User-table. For example in SQL something like: ::

	$ sqlite3 data.db
	# or psql equivalent for Postgres

	sqlite> UPDATE user SET password = '<above hash-value>' WHERE username == 'myusername';

Build Documentation
-------------------

Open a command line, (if needed activate your virtualenv) and move into the directory  ``GeoHealthCheck/doc/``.
In there, type ``make html`` plus ENTER and the documentation should be built locally.
