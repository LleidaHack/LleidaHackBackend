"""empty message

Revision ID: 96f1efb16d44
Revises: 7658a0220b59
Create Date: 2024-09-20 14:18:41.822931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '96f1efb16d44'
down_revision = '7658a0220b59'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hacker_event_registration', sa.Column('wants_credit', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('hacker_event_registration', 'wants_credit')
    # ### end Alembic commands ###
