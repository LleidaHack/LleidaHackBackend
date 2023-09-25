"""empty message

Revision ID: bf4093e132a0
Revises: 6e8d8784987c
Create Date: 2023-09-25 13:03:44.855290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bf4093e132a0'
down_revision = '6e8d8784987c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('hacker', sa.Column('studies', sa.String(), nullable=True))
    op.add_column('hacker', sa.Column('study_center', sa.String(), nullable=True))
    op.add_column('hacker', sa.Column('location', sa.String(), nullable=True))
    op.add_column('hacker', sa.Column('how_did_you_meet_us', sa.String(), nullable=True))
    op.add_column('hacker_event_registration', sa.Column('studies', sa.String(), nullable=True))
    op.add_column('hacker_event_registration', sa.Column('study_center', sa.String(), nullable=True))
    op.add_column('hacker_event_registration', sa.Column('location', sa.String(), nullable=True))
    op.add_column('hacker_event_registration', sa.Column('how_did_you_meet_us', sa.String(), nullable=True))
    op.add_column('hacker_event_registration', sa.Column('confirmed_assistance', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_user_telephone'), 'user', ['telephone'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    #set user telephone end with it's id to avoid unique constraint error
    op.drop_index(op.f('ix_user_telephone'), table_name='user')
    op.drop_column('hacker_event_registration', 'confirmed_assistance')
    op.drop_column('hacker_event_registration', 'how_did_you_meet_us')
    op.drop_column('hacker_event_registration', 'location')
    op.drop_column('hacker_event_registration', 'study_center')
    op.drop_column('hacker_event_registration', 'studies')
    op.drop_column('hacker', 'how_did_you_meet_us')
    op.drop_column('hacker', 'location')
    op.drop_column('hacker', 'study_center')
    op.drop_column('hacker', 'studies')
    # ### end Alembic commands ###
