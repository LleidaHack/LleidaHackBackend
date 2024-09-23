"""empty message

Revision ID: 082e0feb242a
Revises: 7658a0220b59
Create Date: 2024-09-23 13:09:02.609817

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '082e0feb242a'
down_revision = '7658a0220b59'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'lleida_hacker_group_leader',
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['group_id'],
            ['lleida_hacker_group.id'],
        ), sa.ForeignKeyConstraint(
            ['user_id'],
            ['lleida_hacker.user_id'],
        ), sa.PrimaryKeyConstraint('group_id', 'user_id'))
    op.add_column('lleida_hacker_group',
                  sa.Column('image', sa.String(), nullable=True))
    op.drop_constraint('lleida_hacker_group_leader_id_fkey',
                       'lleida_hacker_group',
                       type_='foreignkey')
    op.drop_column('lleida_hacker_group', 'leader_id')
    op.add_column('lleida_hacker_group_user',
                  sa.Column('primary', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lleida_hacker_group_user', 'primary')
    op.add_column(
        'lleida_hacker_group',
        sa.Column('leader_id',
                  sa.INTEGER(),
                  autoincrement=False,
                  nullable=True))
    op.create_foreign_key('lleida_hacker_group_leader_id_fkey',
                          'lleida_hacker_group', 'lleida_hacker',
                          ['leader_id'], ['user_id'])
    op.drop_column('lleida_hacker_group', 'image')
    op.drop_table('lleida_hacker_group_leader')
    # ### end Alembic commands ###