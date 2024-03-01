"""empty message

Revision ID: 758241c4720f
Revises: 2bb7aa776103
Create Date: 2024-03-01 17:46:02.205394

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '758241c4720f'
down_revision = '2bb7aa776103'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user-config', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'user-config', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user-config', type_='foreignkey')
    op.drop_column('user-config', 'user_id')
    # ### end Alembic commands ###