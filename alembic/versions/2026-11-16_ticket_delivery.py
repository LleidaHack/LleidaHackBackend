"""Track ticket delivery for mentors and staff without participant registrations."""

import sqlalchemy as sa

from alembic import op

revision = "20261116_ticket_delivery"
down_revision = "20261115_release_reminder"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_mentor", sa.Column("invitation_email", sa.String(254), nullable=True)
    )
    op.create_table(
        "event_ticket_delivery",
        sa.Column(
            "event_id", sa.Integer(), sa.ForeignKey("event.id"), primary_key=True
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("my_user.id"), primary_key=True
        ),
        sa.Column("ticket_sent_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("event_mentor", "invitation_email")
    op.drop_table("event_ticket_delivery")
