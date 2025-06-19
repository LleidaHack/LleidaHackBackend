"""empty message

Revision ID: beb25bc83663
Revises: 20e9f9db44d3
Create Date: 2024-03-18 15:55:53.658046

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "beb25bc83663"
down_revision = "20e9f9db44d3"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("user", "my_user")


def downgrade():
    op.rename_table("my_user", "user")
