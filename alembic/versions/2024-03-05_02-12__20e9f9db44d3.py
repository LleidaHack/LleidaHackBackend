"""empty message

Revision ID: 20e9f9db44d3
Revises: 6a212e0e0b92
Create Date: 2024-03-05 02:12:49.042601

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '20e9f9db44d3'
down_revision = '6a212e0e0b92'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_role_id', table_name='role')
    op.drop_index('ix_role_name', table_name='role')
    op.drop_table('role')
    op.drop_column('hacker_event_registration', 'dailyhack_url')
    op.execute('DROP TYPE IF EXISTS roleenum;')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'hacker_event_registration',
        sa.Column('dailyhack_url',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True))
    op.create_table(
        'role',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('name',
                  postgresql.ENUM('Admin', 'User', 'Guest', name='roleenum'),
                  autoincrement=False,
                  nullable=True),
        sa.PrimaryKeyConstraint('id', name='role_pkey'))
    op.create_index('ix_role_name', 'role', ['name'], unique=False)
    op.create_index('ix_role_id', 'role', ['id'], unique=False)
    # ### end Alembic commands ###