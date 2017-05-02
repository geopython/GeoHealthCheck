# Flask script mainly for managing the DB
# Credits: https://github.com/miguelgrinberg
# See https://flask-migrate.readthedocs.io/en/latest/
# and https://blog.miguelgrinberg.com/post/
#  flask-migrate-alembic-database-migration-wrapper-for-flask/page/3
#
# Usage:
#
# $ python manage.py --help
# usage: manage.py [-h] {shell,db,runserver} ...
#
# positional arguments:
#   {shell,db,runserver}
#     shell     Runs a Python shell inside Flask application context.
#     db        Perform database migrations
#     runserver Runs the Flask development server i.e. app.run()
#
# optional arguments:
#   -h, --help  show this help message and exit
#
# For DB management:
# $ python manage.py db --help
# usage: Perform database migrations
#
# positional arguments:
#   {upgrade,migrate,current,stamp,init,downgrade,history,revision}
#     upgrade         Upgrade to a later version
#     migrate         Alias for 'revision --autogenerate'
#     current         Display the current revision for each database.
#     stamp 'stamp' the revision table with the given revision;
# dont run any migrations
#     init  Generates a new migration
#     downgrade       Revert to a previous version
#     history         List changeset scripts in chronological order.
#     revision        Create a new revision file.
#
# optional arguments:
#   -h, --help  show this help message and exit

from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from init import DB, APP

migrate = Migrate(APP, DB)

manager = Manager(APP)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
