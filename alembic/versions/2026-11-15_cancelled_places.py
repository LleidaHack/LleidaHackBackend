"""Retain cancelled registrations while releasing their accepted place."""

import sqlalchemy as sa

from alembic import op

revision = "20261115_cancelled_places"
down_revision = "20261110_event_readiness"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hacker_event_registration",
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("hacker_event_registration", "cancelled_at")
