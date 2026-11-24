"""Event guests: roster-only identities that receive a "Convidat" ticket."""

import sqlalchemy as sa

from alembic import op

revision = "20261124_event_guests"
down_revision = "20261121_mlh_consent"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("ck_user_access_role", "my_user", type_="check")
    op.create_check_constraint(
        "ck_user_access_role",
        "my_user",
        "access_role IN ('superadmin','admin','lleidahacker','hacker','mentor','guest')",
    )
    op.create_table(
        "event_guest",
        sa.Column(
            "event_id", sa.Integer(), sa.ForeignKey("event.id"), primary_key=True
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("my_user.id"), primary_key=True
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade():
    if (
        op.get_bind()
        .execute(
            sa.text("SELECT EXISTS(SELECT 1 FROM my_user WHERE access_role='guest')")
        )
        .scalar()
    ):
        raise RuntimeError("Export and remove guest records before downgrading")
    op.drop_table("event_guest")
    op.drop_constraint("ck_user_access_role", "my_user", type_="check")
    op.create_check_constraint(
        "ck_user_access_role",
        "my_user",
        "access_role IN ('superadmin','admin','lleidahacker','hacker','mentor')",
    )
