"""Record when a hacker registered for an event."""

import sqlalchemy as sa

from alembic import op

revision = "20261010_registered_at"
down_revision = "20260918_vouchers"
branch_labels = None
depends_on = None


def upgrade():
    # Existing rows stay NULL: their real registration time is unknown.
    op.add_column(
        "hacker_event_registration",
        sa.Column("registered_at", sa.DateTime(), nullable=True),
    )
    op.alter_column(
        "hacker_event_registration", "registered_at", server_default=sa.func.now()
    )


def downgrade():
    op.drop_column("hacker_event_registration", "registered_at")
