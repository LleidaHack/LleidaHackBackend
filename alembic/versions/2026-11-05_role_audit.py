"""Audit global role changes independently from event editions."""

import sqlalchemy as sa

from alembic import op

revision = "20261105_role_audit"
down_revision = "20261105_user_access"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "access_role_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("my_user.id")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("my_user.id"), nullable=False),
        sa.Column("previous_role", sa.String(30), nullable=False),
        sa.Column("new_role", sa.String(30), nullable=False),
        sa.Column("reason", sa.String(500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_access_role_audit_user_id", "access_role_audit", ["user_id"])


def downgrade():
    op.drop_table("access_role_audit")
