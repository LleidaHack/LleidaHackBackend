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
                    sa.Column('leader_id', sa.Integer(), sa.ForeignKey('hacker.user_id'), nullable=True),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('description', sa.String(length=50), nullable=True),
    )
    op.create_table('hacker_group_user',
                    sa.Column('hacker_id', sa.Integer(), sa.ForeignKey('hacker.user_id'), primary_key=True),
                    sa.Column('group_id', sa.Integer(), sa.ForeignKey('hacker_group.id'), primary_key=True),
    )
    op.create_table('lleida_hacker_group',
                    sa.Column('id', sa.Integer(), primary_key=True, index=True),
                    sa.Column('leader_id', sa.Integer(), sa.ForeignKey('lleida_hacker.user_id'), nullable=True),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('description', sa.String(length=50), nullable=True),
    )
    op.create_table('lleida_hacker_group_user',
                    sa.Column('user_id', sa.Integer(), sa.ForeignKey('lleida_hacker.user_id'), primary_key=True),
                    sa.Column('group_id', sa.Integer(), sa.ForeignKey('lleida_hacker_group.id'), primary_key=True),
    )
    #add leaders
    # op.add_column('lleida_hacker_group', sa.Column('leader', sa.Integer(), sa.ForeignKey('lleida_hacker.user_id'), nullable=False))
    # op.add_column('hacker_group', sa.column('leader', sa.Integer(), sa.ForeignKey('hacker.user_id')))
    # op.add_column('lleida_hacker_group', sa.column('leader', sa.Integer(), sa.ForeignKey('lleida_hacker.user_id')))



def downgrade():
    op.drop_table('lleida_hacker_group_users')
    op.drop_table('lleida_hacker_group')
    op.drop_table('hacker_group_users')
    op.drop_table('hacker_group')
