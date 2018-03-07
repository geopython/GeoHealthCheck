"""empty message

Revision ID: 2638c2a40625
Revises: 992013af402f
Create Date: 2017-09-08 10:48:19.596099

"""
from alembic import op
import sqlalchemy as sa
import imp
import os
from GeoHealthCheck.migrations import alembic_helpers

# revision identifiers, used by Alembic.
revision = '2638c2a40625'
down_revision = '992013af402f'
branch_labels = None
depends_on = None


def upgrade():
    if not alembic_helpers.table_has_column('resource', 'active'):
        print('Column active not present in resource table, will create')
        op.add_column(u'resource', sa.Column('active', sa.Boolean(),
                      nullable=False, default=1, server_default='True'))
    else:
        print('Column active already present in resource table')


def downgrade():
    print('Dropping Column active from resource table')
    op.drop_column(u'resource', 'active')
