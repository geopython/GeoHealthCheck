"""empty message

Revision ID: 90e1c865a561
Revises: 34531bfd7cab
Create Date: 2018-11-15 21:51:51.569697

"""
from GeoHealthCheck.init import App
from GeoHealthCheck.models import User
DB = App.get_db()


# revision identifiers, used by Alembic.
revision = '90e1c865a561'
down_revision = '34531bfd7cab'
branch_labels = None
depends_on = None


def upgrade():
    users = User.query.all()
    for user in users:
        # May happen when adding users before upgrade
        if len(user.password) > 80:
            print('NOT Encrypting for: %s' % user.username)
            continue
        print('Encrypting for user: %s' % user.username)
        user.set_password(user.password)
    DB.session.commit()


def downgrade():
    print('Sorry. we cannot downgrade from encrypted passwords for obvious reasons.')
