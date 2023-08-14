"""add user types

Revision ID: 6ddf31156252
Revises: 60146f40bc17
Create Date: 2022-05-27 16:30:39.595984

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6ddf31156252'
down_revision = '60146f40bc17'
branch_labels = None
depends_on = None


def upgrade():

    op.add_column('llhk_user',
                  sa.Column('type', sa.String(length=50), nullable=True))
    op.execute("UPDATE llhk_user SET type = 'llhk_user'")
    op.alter_column('llhk_user', 'type', nullable=False)
    op.create_table(
        'lleida_hacker',
        sa.Column('user_id',
                  sa.Integer(),
                  sa.ForeignKey('llhk_user.id'),
                  primary_key=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('nif', sa.String(length=50), nullable=False),
        sa.Column('student', sa.Boolean(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('image_id', sa.String(), nullable=False),
        sa.Column('github', sa.String(length=50), nullable=False),
    )
    op.create_table(
        'company',
        sa.Column('user_id',
                  sa.Integer(),
                  sa.ForeignKey('llhk_user.id'),
                  primary_key=True),
        sa.Column('logo', sa.String(), nullable=False),
        sa.Column('description', sa.String(length=50), nullable=False),
    )
    op.create_table(
        'hacker',
        sa.Column('user_id',
                  sa.Integer(),
                  sa.ForeignKey('llhk_user.id'),
                  primary_key=True),
        sa.Column('banned', sa.Integer(), nullable=False),
        sa.Column('github', sa.String(length=50), nullable=False),
        sa.Column('linkedin', sa.String(length=50), nullable=True),
    )


def downgrade():
    op.drop_column('llhk_user', 'type')
    op.drop_table('lleida_hacker')
    op.drop_table('company')
    op.drop_table('hacker')
