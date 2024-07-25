"""empty message

Revision ID: a19f3a547386
Revises: e3649247c1ec
Create Date: 2024-07-25 17:04:02.344697

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a19f3a547386'
down_revision = 'e3649247c1ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('lleida_hacker', sa.Column('linkedin', sa.String(), default=''))
    op.execute("UPDATE lleida_hacker SET linkedin='test'")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('lleida_hacker', 'linkedin')
    # ### end Alembic commands ###
