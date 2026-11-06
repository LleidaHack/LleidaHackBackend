"""Audited nickname approval requests."""

import sqlalchemy as sa

from alembic import op

revision = "20261106_nicknames"
down_revision = "20261106_challenge_votes"
branch_labels = depends_on = None


def upgrade():
    op.add_column(
        "event_voucher",
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "nickname_request",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("my_user.id"), nullable=False),
        sa.Column("previous", sa.String(), nullable=False),
        sa.Column("proposed", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("my_user.id")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_nickname_request_user_id", "nickname_request", ["user_id"])
    op.create_index(
        "uq_nickname_pending",
        "nickname_request",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade():
    op.drop_column("event_voucher", "revoked")
    op.drop_table("nickname_request")
