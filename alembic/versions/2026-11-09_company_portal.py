"""Add isolated company judging accounts and optional imported project details."""

import sqlalchemy as sa

from alembic import op

revision = "20261109_company_portal"
down_revision = "20261107_group_cascade"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "company_portal_account",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("company.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(500)),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "company_portal_grant",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("company_portal_account.id"),
            nullable=False,
        ),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("rooms", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column(
            "winner_id",
            sa.Integer(),
            sa.ForeignKey("hacker_group.id", ondelete="SET NULL"),
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("account_id", "event_id"),
    )
    op.create_table(
        "company_portal_session",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("company_portal_account.id"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "company_portal_invitation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("operation_id", sa.String(36), nullable=False, unique=True),
        sa.Column(
            "account_id",
            sa.Integer(),
            sa.ForeignKey("company_portal_account.id"),
            nullable=False,
        ),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed", sa.Boolean(), nullable=False),
        sa.Column("delivery_state", sa.String(30), nullable=False),
        sa.Column("delivery_url", sa.Text()),
        sa.Column("mail_id", sa.Integer()),
        sa.Column("fingerprint", sa.String(64), nullable=False),
    )
    op.create_table(
        "company_portal_note",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "grant_id",
            sa.Integer(),
            sa.ForeignKey("company_portal_grant.id"),
            nullable=False,
        ),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("hacker_group.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer()),
        sa.Column("favorite", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("grant_id", "group_id"),
    )
    for name, size in (
        ("description", 10000),
        ("repository_url", 500),
        ("demo_url", 500),
    ):
        op.add_column(
            "event_devpost_project",
            sa.Column(name, sa.String(size), nullable=False, server_default=""),
        )


def downgrade():
    for name in ("demo_url", "repository_url", "description"):
        op.drop_column("event_devpost_project", name)
    for name in ("note", "invitation", "session", "grant", "account"):
        op.drop_table("company_portal_" + name)
