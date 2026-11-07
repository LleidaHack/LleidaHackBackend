"""Durable alert queue for the official Discord bot."""

import sqlalchemy as sa

from alembic import op

revision = "20261105_discord_outbox"
down_revision = "20261105_role_audit"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_discord_delivery",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("alert_id", sa.String(100), unique=True, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.String(100)),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("message_id", sa.String(100)),
        sa.Column("error", sa.String(500)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_event_discord_delivery_event_id", "event_discord_delivery", ["event_id"]
    )


def downgrade():
    op.drop_table("event_discord_delivery")
