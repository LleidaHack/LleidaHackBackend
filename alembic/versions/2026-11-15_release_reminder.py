"""Track release reminder delivery and reuse queued mail on retry."""

import sqlalchemy as sa

from alembic import op

revision = "20261115_release_reminder"
down_revision = "20261115_cancelled_places"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hacker_event_registration",
        sa.Column("release_reminder_sent_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "hacker_event_registration",
        sa.Column("release_reminder_mail_id", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column("hacker_event_registration", "release_reminder_mail_id")
    op.drop_column("hacker_event_registration", "release_reminder_sent_at")
