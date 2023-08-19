"""empty message

Revision ID: 50b286a567e5
Revises: 9f8fb6880207
Create Date: 2023-08-19 03:46:17.688045

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50b286a567e5'
down_revision = '9f8fb6880207'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('company_user', sa.Column('accepted', sa.Boolean(), nullable=True))
    op.add_column('company_user', sa.Column('rejected', sa.Boolean(), nullable=True))
    op.add_column('lleida_hacker', sa.Column('accepted', sa.Boolean(), nullable=True))
    op.add_column('lleida_hacker', sa.Column('rejected', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lleida_hacker', 'rejected')
    op.drop_column('lleida_hacker', 'accepted')
    op.drop_column('company_user', 'rejected')
    op.drop_column('company_user', 'accepted')
    # ### end Alembic commands ###
