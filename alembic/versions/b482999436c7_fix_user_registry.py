"""fix user registry

Revision ID: b482999436c7
Revises: 9eea0522e1bc
Create Date: 2022-07-15 19:29:57.557370

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b482999436c7'
down_revision = '9eea0522e1bc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'hacker_event_registration',
        sa.Column('user_id',
                  sa.Integer(),
                  sa.ForeignKey('hacker.user_id'),
                  primary_key=True),
        sa.Column('event_id',
                  sa.Integer(),
                  sa.ForeignKey('event.id'),
                  primary_key=True),
    )


def downgrade():
    op.drop_table('hacker_event_registration')
