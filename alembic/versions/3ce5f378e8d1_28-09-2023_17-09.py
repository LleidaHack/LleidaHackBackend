"""empty message

Revision ID: 3ce5f378e8d1
Revises: 66f272fcd052
Create Date: 2023-09-28 17:09:52.507849

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ce5f378e8d1'
down_revision = '66f272fcd052'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hacker_event_registration', sa.Column('confirmed_assistance_token', sa.String(), nullable=True))
    op.alter_column('user', 'terms_accepted',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'terms_accepted',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.drop_column('hacker_event_registration', 'confirmed_assistance_token')
    # ### end Alembic commands ###
