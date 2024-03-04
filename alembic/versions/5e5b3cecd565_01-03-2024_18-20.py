"""empty message

Revision ID: 5e5b3cecd565
Revises: a2ac322dab0a
Create Date: 2024-03-01 18:20:53.669575

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5e5b3cecd565'
down_revision = 'a2ac322dab0a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('config_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'user', 'user-config', ['config_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'user', type_='foreignkey')
    op.drop_column('user', 'config_id')
    # ### end Alembic commands ###
