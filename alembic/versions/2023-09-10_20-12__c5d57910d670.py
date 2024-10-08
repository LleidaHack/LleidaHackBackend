"""empty message

Revision ID: c5d57910d670
Revises: 6fa69e6756c5
Create Date: 2023-09-10 20:12:08.846275

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'c5d57910d670'
down_revision = '6fa69e6756c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event',
                  sa.Column('max_group_size', sa.Integer(), nullable=True))
    op.add_column('event', sa.Column('is_open', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('event', 'is_open')
    op.drop_column('event', 'max_group_size')
    # ### end Alembic commands ###
