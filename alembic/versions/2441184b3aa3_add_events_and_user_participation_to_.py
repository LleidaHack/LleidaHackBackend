"""add events and user participation to those

Revision ID: 2441184b3aa3
Revises: fd381ce9b8dd
Create Date: 2022-06-07 11:58:12.139856

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2441184b3aa3'
down_revision = 'fd381ce9b8dd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('event',
                    sa.Column('id', sa.Integer(), primary_key=True, index=True),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('description', sa.String(length=500), nullable=False),
                    sa.Column('start_date', sa.DateTime(), nullable=False),
                    sa.Column('end_date', sa.DateTime(), nullable=False),
                    sa.Column('location', sa.String(length=50), nullable=False),
                    sa.Column('archived', sa.Boolean(), nullable=False, default=False),
                    sa.Column('status', sa.Integer(), nullable=False, default=0),
                    sa.Column('price', sa.Integer(), nullable=False, default=0),
                    sa.Column('max_participants', sa.Integer(), nullable=False, default=0),
                    sa.Column('max_sponsors', sa.Integer(), nullable=False, default=0),
                    # sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
                    # sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now()),
    )
    op.create_table('hacker_event_participation',
                    sa.Column('user_id', sa.Integer(), sa.ForeignKey('hacker.user_id'), primary_key=True),
                    sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), primary_key=True),
    )
    op.create_table('hacker_group_event_participation',
                    sa.Column('user_id', sa.Integer(), sa.ForeignKey('hacker_group.id'), primary_key=True),
                    sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), primary_key=True),
    )
    op.create_table('lleida_hacker_event_participation',
                    sa.Column('user_id', sa.Integer(), sa.ForeignKey('lleida_hacker.user_id'), primary_key=True),
                    sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), primary_key=True),
    )
    op.create_table('company_event_participation',
                    sa.Column('company_id', sa.Integer(), sa.ForeignKey('company.id'), primary_key=True),
                    sa.Column('event_id', sa.Integer(), sa.ForeignKey('event.id'), primary_key=True),
    )


def downgrade():
    op.drop_table('hacker_event_participation')
    op.drop_table('hacker_group_event_participation')
    op.drop_table('lleida_hacker_event_participation')
    op.drop_table('company_event_participation')
    op.drop_table('event')