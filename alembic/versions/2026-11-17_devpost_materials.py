"""Preserve project descriptions, links and technologies from Devpost exports."""

from alembic import op
import sqlalchemy as sa

revision = "20261117_devpost_materials"
down_revision = "20261117_release_queue"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_devpost_project",
        sa.Column("materials", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.alter_column("event_devpost_project", "description", type_=sa.Text())


def downgrade():
    op.alter_column("event_devpost_project", "description", type_=sa.String(10000))
    op.drop_column("event_devpost_project", "materials")
