"""Store sponsor tiers and ordering per event edition."""

import sqlalchemy as sa

from alembic import op

revision = "20260916_sponsors"
down_revision = "eb5796b93841"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event", sa.Column("schedule", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "event", sa.Column("activities", sa.JSON(), nullable=False, server_default="[]")
    )
    op.add_column(
        "company_event_participation", sa.Column("tier", sa.Integer(), nullable=True)
    )
    op.add_column(
        "company_event_participation",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        "UPDATE company_event_participation AS p SET tier = c.tier FROM company AS c WHERE p.company_id = c.id"
    )


def downgrade():
    op.drop_column("event", "activities")
    op.drop_column("event", "schedule")
    op.drop_column("company_event_participation", "display_order")
    op.drop_column("company_event_participation", "tier")
