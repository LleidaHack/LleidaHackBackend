"""empty message

Revision ID: 871f7124284f
Revises: 8d4c32422e7a
Create Date: 2023-09-15 16:44:24.490880

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '871f7124284f'
down_revision = '8d4c32422e7a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('hacker', 'is_verified')
    op.add_column('user', sa.Column('is_verified', sa.Boolean(),
                                    nullable=True))
    op.add_column('user',
                  sa.Column('verification_token', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'verification_token')
    op.drop_column('user', 'is_verified')
    op.add_column(
        'hacker',
        sa.Column('is_verified',
                  sa.BOOLEAN(),
                  autoincrement=False,
                  nullable=True))
    # ### end Alembic commands ###
