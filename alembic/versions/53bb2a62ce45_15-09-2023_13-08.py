"""empty message

Revision ID: 53bb2a62ce45
Revises: 4b8ee8394bcb
Create Date: 2023-09-15 13:08:06.408450

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53bb2a62ce45'
down_revision = '4b8ee8394bcb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_user_email', 'user', ['email'], unique=True)
    op.create_index('ix_user_nickname', 'user', ['nickname'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    op.drop_index('ix_user_nickname', table_name='user')
    op.drop_index('ix_user_email', table_name='user')
    # ### end Alembic commands ###
