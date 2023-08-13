"""add meals

Revision ID: 9eea0522e1bc
Revises: 2441184b3aa3
Create Date: 2022-06-20 11:31:36.033179

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9eea0522e1bc'
down_revision = '2441184b3aa3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'meal',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('event_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
    )
    op.create_table(
        'hacker_meal',
        sa.Column('user_id',
                  sa.Integer(),
                  sa.ForeignKey('hacker.user_id'),
                  primary_key=True,
                  index=True),
        sa.Column('meal_id',
                  sa.Integer(),
                  sa.ForeignKey('meal.id'),
                  primary_key=True,
                  index=True),
    )


def downgrade():
    op.drop_table('hacker_meal')
    op.drop_table('meal')
