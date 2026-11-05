"""Allow access-role assignment without changing participant account identity."""

import sqlalchemy as sa

from alembic import op

revision = "20261105_user_access"
down_revision = "20261105_access_roles"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "my_user",
        sa.Column(
            "access_role", sa.String(30), nullable=False, server_default="hacker"
        ),
    )
    op.execute(
        "UPDATE my_user u SET access_role = l.access_role FROM lleida_hacker l WHERE l.user_id = u.id"
    )
    op.create_check_constraint(
        "ck_user_access_role",
        "my_user",
        "access_role IN ('superadmin','admin','lleidahacker','hacker')",
    )
    op.drop_constraint("ck_staff_access_role", "lleida_hacker", type_="check")
    op.drop_column("lleida_hacker", "access_role")


def downgrade():
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT 1 FROM my_user WHERE access_role != 'hacker' AND id NOT IN (SELECT user_id FROM lleida_hacker) LIMIT 1"
            )
        )
        .first()
    ):
        raise RuntimeError(
            "Cannot discard access roles assigned to participant accounts"
        )
    op.add_column(
        "lleida_hacker",
        sa.Column(
            "access_role", sa.String(30), nullable=False, server_default="lleidahacker"
        ),
    )
    op.execute(
        "UPDATE lleida_hacker l SET access_role = CASE WHEN u.access_role = 'hacker' THEN 'lleidahacker' ELSE u.access_role END FROM my_user u WHERE u.id = l.user_id"
    )
    op.create_check_constraint(
        "ck_staff_access_role",
        "lleida_hacker",
        "access_role IN ('superadmin','admin','lleidahacker')",
    )
    op.drop_constraint("ck_user_access_role", "my_user", type_="check")
    op.drop_column("my_user", "access_role")
