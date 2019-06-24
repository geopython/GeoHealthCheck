"""empty message

Revision ID: f72ff1ac3967
Revises: 90e1c865a561
Create Date: 2019-06-24 09:33:20.664465

"""
from alembic import op
import sqlalchemy as sa
from GeoHealthCheck.migrations import alembic_helpers

# revision identifiers, used by Alembic.
revision = 'f72ff1ac3967'
down_revision = '90e1c865a561'
branch_labels = None
depends_on = None



def upgrade():
    if not alembic_helpers.table_has_column('resource', 'auth'):
        print('Column auth not present in resource table, will create')
        op.add_column(u'resource', sa.Column('auth', sa.Text(),
                      nullable=True, default=None, server_default=None))
    else:
        print('Column auth already present in resource table')


def downgrade():
    print('Dropping Column auth from resource table')
    op.drop_column(u'resource', 'auth')
