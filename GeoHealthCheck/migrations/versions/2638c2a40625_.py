"""empty message

Revision ID: 2638c2a40625
Revises: 992013af402f
Create Date: 2017-09-08 10:48:19.596099

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2638c2a40625'
down_revision = '992013af402f'
branch_labels = None
depends_on = None

alembic_helpers = imp.load_source('alembic_helpers', (
os.getcwd() + '/' + op.get_context().script.dir + '/alembic_helpers.py'))

def upgrade():
    if not alembic_helpers.table_has_column('resource', 'active'):
        from sqlalchemy.sql import table, column
        print('Column active not present in resource table, will create')
        op.add_column(u'resource', sa.Column('active', sa.Boolean, nullable=True, default=True))
        resource = table('resource', column('active'))
        op.execute(resource.update().values(active=True))
        op.alter_column('resource', 'active', nullable=False)
    else:
        print('Column active already present in resource table')


def downgrade():
    print('Dropping Column active from resource table')
    op.drop_column(u'resource', 'active')
