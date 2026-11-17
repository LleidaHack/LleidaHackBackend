"""Allow Devpost submissions to wait for manual team assignment."""

import sqlalchemy as sa

from alembic import op

revision = "20261117_pending_devpost"
down_revision = "20261117_ribo_room"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("event_devpost_project", "group_id", nullable=True)
    op.add_column(
        "event_devpost_project",
        sa.Column(
            "submitted_team_code", sa.String(100), nullable=False, server_default=""
        ),
    )


def downgrade():
    # PostgreSQL refuses the downgrade while unmatched projects still exist.
    op.alter_column("event_devpost_project", "group_id", nullable=False)
    op.drop_column("event_devpost_project", "submitted_team_code")
