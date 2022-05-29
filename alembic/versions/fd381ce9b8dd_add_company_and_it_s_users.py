"""add company and it's users

Revision ID: fd381ce9b8dd
Revises: 97d6460ed6e5
Create Date: 2022-05-29 12:17:47.868737

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd381ce9b8dd'
down_revision = '97d6460ed6e5'
branch_labels = None
depends_on = None


def upgrade():
    pass
    # op.rename_table('company', 'company_user')
    # op.create_table('company',
    #                 sa.Column('id', sa.Integer(), primary_key=True, index=True),
    #                 sa.Column('name', sa.String(), nullable=False),
    #                 sa.Column('logo', sa.String(), nullable=False),
    #                 sa.Column('description', sa.String(), nullable=False),
    # )
    # op.add_column('company_user', sa.Column('company_id', sa.Integer(), sa.ForeignKey('company.id'), nullable=False))

def downgrade():
    pass
