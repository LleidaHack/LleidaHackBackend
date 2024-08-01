"""empty message

Revision ID: a67851c0d7d4
Revises: 3ce5f378e8d1
Create Date: 2023-09-28 18:34:24.669087

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'a67851c0d7d4'
down_revision = '3ce5f378e8d1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'hacker_event_registration',
        sa.Column('confirm_assistance_token', sa.String(), nullable=True))
    op.drop_column('hacker_event_registration', 'confirmed_assistance_token')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'hacker_event_registration',
        sa.Column('confirmed_assistance_token',
                  sa.VARCHAR(),
                  autoincrement=False,
                  nullable=True))
    op.drop_column('hacker_event_registration', 'confirm_assistance_token')
    # ### end Alembic commands ###
