"""Actual presentation times for badge-driven room queues."""

import sqlalchemy as sa

from alembic import op

revision = "20261106_judging_runtime"
down_revision = "20261106_nicknames"
branch_labels = depends_on = None


def upgrade():
    op.add_column(
        "event_presentation", sa.Column("started_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "event_presentation", sa.Column("completed_at", sa.DateTime(timezone=True))
    )


def downgrade():
    op.drop_column("event_presentation", "completed_at")
    op.drop_column("event_presentation", "started_at")
