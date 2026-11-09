"""Allow company judges to extend presentation time without changing its start."""

import sqlalchemy as sa

from alembic import op

revision = "20261109_company_timer"
down_revision = "20261109_company_portal"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_presentation",
        sa.Column(
            "duration_seconds", sa.Integer(), nullable=False, server_default="300"
        ),
    )


def downgrade():
    op.drop_column("event_presentation", "duration_seconds")
