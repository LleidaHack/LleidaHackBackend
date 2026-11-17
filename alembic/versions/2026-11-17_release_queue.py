"""Persist organizer-requested release reminders."""

import sqlalchemy as sa

from alembic import op

revision = "20261117_release_queue"
down_revision = "20261116_ticket_delivery"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hacker_event_registration", sa.Column("release_queue_state", sa.String(16))
    )
    op.add_column(
        "hacker_event_registration", sa.Column("release_queue_actor", sa.Integer())
    )
    op.create_index(
        "ix_hacker_event_registration_release_queue_state",
        "hacker_event_registration",
        ["release_queue_state"],
    )


def downgrade():
    op.drop_index(
        "ix_hacker_event_registration_release_queue_state",
        table_name="hacker_event_registration",
    )
    op.drop_column("hacker_event_registration", "release_queue_actor")
    op.drop_column("hacker_event_registration", "release_queue_state")
