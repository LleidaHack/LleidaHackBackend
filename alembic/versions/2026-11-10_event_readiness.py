"""Event incidents and finalized company decisions."""

import sqlalchemy as sa

from alembic import op

revision = "20261110_event_readiness"
down_revision = "20261109_company_timer"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "company_portal_grant",
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "event_incident",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("details", sa.String(2000), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_event_incident_event_id", "event_incident", ["event_id"])


def downgrade():
    op.drop_table("event_incident")
    op.drop_column("company_portal_grant", "finalized_at")
