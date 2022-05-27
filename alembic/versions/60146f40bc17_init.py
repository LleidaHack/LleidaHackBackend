"""init

Revision ID: 60146f40bc17
Revises: 
Create Date: 2022-05-27 15:52:58.697936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '60146f40bc17'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('llhk_user',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('nickname', sa.String(length=50), nullable=False),
                    sa.Column('password', sa.String(length=50), nullable=False),
                    sa.Column('birthdate', sa.Date(), nullable=False),
                    sa.Column('food_restrictions', sa.String(length=50), nullable=False),
                    sa.Column('email', sa.String(length=50), nullable=False),
                    sa.Column('telephone', sa.String(length=50), nullable=False),
                    sa.Column('address', sa.String(length=50), nullable=False),
                    sa.Column('shirt_size', sa.String(length=50), nullable=False),
    )


def downgrade():
    op.drop_table('llhk_user')
