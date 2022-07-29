"""image_id fix

Revision ID: bb840e8a133f
Revises: 12a91ff3996b
Create Date: 2022-07-29 20:03:36.512686

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb840e8a133f'
down_revision = '12a91ff3996b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('llhk_user', sa.Column('image_id', sa.String(), nullable=True))
    op.execute("UPDATE llhk_user SET image_id = 'none'")
    op.alter_column('llhk_user', 'image_id', nullable=False)

def downgrade():
    op.drop_column('llhk_user', 'image_id')
