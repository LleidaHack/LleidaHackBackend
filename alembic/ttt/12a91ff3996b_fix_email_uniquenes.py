"""fix email uniquenes

Revision ID: 12a91ff3996b
Revises: b482999436c7
Create Date: 2022-07-15 20:41:46.420023

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '12a91ff3996b'
down_revision = 'b482999436c7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint('uq_email', 'llhk_user', ['email'])


def downgrade():
    op.drop_constraint('uq_email', 'llhk_user', type_='unique')
