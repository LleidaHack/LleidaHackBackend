"""Link organizer-reviewed Devpost submissions to event teams."""

import sqlalchemy as sa

from alembic import op

revision = "20261106_devpost"
down_revision = "20261105_discord_outbox"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_devpost_project",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column(
            "group_id", sa.Integer(), sa.ForeignKey("hacker_group.id"), nullable=False
        ),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("challenge", sa.String(80), nullable=False),
        sa.Column("mlh", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("event_id", "url"),
        sa.UniqueConstraint("event_id", "group_id"),
    )
    op.create_index(
        "ix_event_devpost_project_event_id", "event_devpost_project", ["event_id"]
    )


def downgrade():
    op.drop_table("event_devpost_project")
