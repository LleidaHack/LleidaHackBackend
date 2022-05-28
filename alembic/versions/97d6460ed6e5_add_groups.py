"""add groups

Revision ID: 97d6460ed6e5
Revises: 6ddf31156252
Create Date: 2022-05-28 15:52:44.805349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97d6460ed6e5'
down_revision = '6ddf31156252'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('hacker_group',
                    sa.Column('id', sa.Integer(), primary_key=True, index=True),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('description', sa.String(length=50), nullable=True),
                    sa.column('leader_id', sa.Integer(), sa.ForeignKey('hacker.user_id')),
    )
    op.create_table('hacker_group_users',
                    sa.Column('hacker_id', sa.Integer(), sa.ForeignKey('hacker.user_id'), primary_key=True),
                    sa.Column('group_id', sa.Integer(), sa.ForeignKey('hacker_group.id'), primary_key=True),
    )
    op.create_table('lleida_hacker_group',
                    sa.Column('id', sa.Integer(), primary_key=True, index=True),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('description', sa.String(length=50), nullable=True),
                    sa.column('leader_id', sa.Integer(), sa.ForeignKey('lleida_hacker.user_id')),
    )
    op.create_table('lleida_hacker_group_users',
                    sa.Column('lleida_hacker_id', sa.Integer(), sa.ForeignKey('lleida_hacker.user_id'), primary_key=True),
                    sa.Column('lleida_hacker_group_id', sa.Integer(), sa.ForeignKey('lleida_hacker_group.id'), primary_key=True),
    )


def downgrade():
    op.drop_table('lleida_hacker_group_users')
    op.drop_table('lleida_hacker_group')
    op.drop_table('hacker_group_users')
    op.drop_table('hacker_group')
