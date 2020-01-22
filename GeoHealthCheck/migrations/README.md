# Database upgrade support

This dir contains various files for developing database upgrades.
Upgrades are supported using Alembic via Flask-Migrate
and Flask-Script.
Users should be able to upgrade existing installs via: 

	# In top dir of installation
	geohc db upgrade
	
The `versions` dir contains the various upgrades. These were
initially created using the Alembic `autogenerate` facility
and modified by hand to adapt to various local circumstances,
mainly to check if particular tables/columns already exist (as
Alembic was introduced later in the project)

The script [manage.py](../manage.py) contains a command processor
for various DB management tasks related to migrations and upgrading.

Whenever a change in the database schema or table content
conventions has changed a new migration should be created via the command.

	python manage.py db migrate

Where `migrate` is an alias for `revision --autogenerate`. 
Alternatively if the autogeneration does not work, create an empty migration: 

	python manage.py db revision
	
In both cases this will create a new revision and a `<revision_number>_.py` file 
under `versions/` to upgrade
to that revision. After this command that `.py` file should be inspected 
and modified where needed. In particular Postgres installations using the
`public` schema should comment out any management of the `spatial_ref_sys` table.
The helper scripts in [alembic_helpers.py](alembic_helpers.py) can be handy 
to check various DB metadata.

Subsequently the upgrade can be performed using:

	python manage.py db upgrade
	# or the equivalent (for users) 
	geohc db upgrade

## Revisions

See the corresponding .py files under `versions`.

### Initial

Initial GHC "version 0" had three tables:

* `user`, `resource` and `run`

### 496427d03f87 - Introduce Tags

Changes: 

* create two new tables: `tag` and `resource_tags`.

### 992013af402f - Introduce Probes and Checks

Changes: 

* create two new tables: `probe_vars` and `check_vars`
* add column `report` to `run` table

### 2638c2a40625 - Add resource.active column

Changes:

* add column `active` to `resource` table
