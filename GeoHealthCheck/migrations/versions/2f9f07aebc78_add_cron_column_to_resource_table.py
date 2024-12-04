"""Add cron column to Resource table

Revision ID: 2f9f07aebc78
Revises: 933717a14052
Create Date: 2024-08-28 04:00:34.863188

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f9f07aebc78'
down_revision = '933717a14052'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('resource', sa.Column('cron', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('resource', 'cron')
