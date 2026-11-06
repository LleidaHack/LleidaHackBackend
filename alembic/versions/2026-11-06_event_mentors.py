"""Meal-only mentors with physical badges and no ticket registration."""

import sqlalchemy as sa

from alembic import op

revision = "20261106_event_mentors"
down_revision = "20261106_judging_runtime"
branch_labels = depends_on = None


def upgrade():
    op.drop_constraint("ck_user_access_role", "my_user", type_="check")
    op.create_check_constraint(
        "ck_user_access_role",
        "my_user",
        "access_role IN ('superadmin','admin','lleidahacker','hacker','mentor')",
    )
    op.create_table(
        "mentor",
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("my_user.id"), primary_key=True
        ),
        *[
            sa.Column(name, sa.String(), nullable=False, server_default="")
            for name in ("github", "linkedin", "cv", "location", "how_did_you_meet_us")
        ],
    )
    op.create_table(
        "event_mentor",
        sa.Column(
            "event_id", sa.Integer(), sa.ForeignKey("event.id"), primary_key=True
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("my_user.id"), primary_key=True
        ),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    for fk in sa.inspect(op.get_bind()).get_foreign_keys("event_voucher"):
        if fk["constrained_columns"] == ["hacker_id"]:
            op.drop_constraint(fk["name"], "event_voucher", type_="foreignkey")
    op.create_foreign_key(
        "fk_event_voucher_user", "event_voucher", "my_user", ["hacker_id"], ["id"]
    )


def downgrade():
    connection = op.get_bind()
    if connection.execute(
        sa.text(
            "SELECT EXISTS(SELECT 1 FROM my_user WHERE type='mentor' OR access_role='mentor') OR EXISTS(SELECT 1 FROM event_voucher v WHERE v.hacker_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM hacker h WHERE h.user_id=v.hacker_id))"
        )
    ).scalar():
        raise RuntimeError("Export and migrate mentor records before downgrading")
    op.drop_constraint("fk_event_voucher_user", "event_voucher", type_="foreignkey")
    op.create_foreign_key(
        "event_voucher_hacker_id_fkey",
        "event_voucher",
        "hacker",
        ["hacker_id"],
        ["user_id"],
    )
    op.drop_constraint("ck_user_access_role", "my_user", type_="check")
    op.create_check_constraint(
        "ck_user_access_role",
        "my_user",
        "access_role IN ('superadmin','admin','lleidahacker','hacker')",
    )
    op.drop_table("event_mentor")
    op.drop_table("mentor")
