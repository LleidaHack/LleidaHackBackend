"""empty message

Revision ID: 2bb7aa776103
Revises: 19a69372d0ba
Create Date: 2024-03-01 17:45:28.356767

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bb7aa776103'
down_revision = '19a69372d0ba'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('user-config_user_id_fkey', 'user-config', type_='foreignkey')
    op.drop_column('user-config', 'user_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user-config', sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key('user-config_user_id_fkey', 'user-config', 'user', ['user_id'], ['id'])
    # ### end Alembic commands ###