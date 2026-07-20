# Flask script mainly for managing the DB
# Credits: https://github.com/miguelgrinberg
# See https://flask-migrate.readthedocs.io/en/latest/
# and https://blog.miguelgrinberg.com/post/
#  flask-migrate-alembic-database-migration-wrapper-for-flask/page/3
#
# Usage:
#
# $ python3 manage.py --help
# usage: manage.py action
#
# optional arguments:
#   -h, --help  show this help message and exit
#
# For DB management:
# $ python manage.py upgrade
# usage: Perform database migrations
#
# action arguments:
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

import sys
import os
from flask_migrate import (Migrate, upgrade, downgrade, current,
                           migrate, history, revision)
from init import App

DB = App.get_db()
APP = App.get_app()
workdir_path = os.path.dirname(__file__)
migrations_path = os.path.join(workdir_path, 'migrations')
Migrate(APP, DB, directory=migrations_path)
ACTIONS = ['current', 'upgrade', 'downgrade', 'migrate', 'history', 'revision']

if __name__ == '__main__':
    if len(sys.argv) < 1 or sys.argv[1] not in ACTIONS:
        print(f'Invalid action, valid values: {ACTIONS}')
        sys.exit(1)

    # Valid action name
    action = sys.argv[1]

    os.chdir(workdir_path)

    with APP.app_context():
        if action == 'current':
            current()
        elif action == 'upgrade':
            # Upgrade to latest version
            upgrade()
        elif action == 'downgrade':
            # Downgrade one version back
            downgrade()
        elif action == 'migrate':
            # Generate revision
            migrate()
        elif action == 'history':
            # Show revisions
            history()
        elif action == 'revision':
            # Create new revision
            revision()
