"""Separate scanner staff, management admins and superadmins."""

import sqlalchemy as sa

from alembic import op

revision = "20261105_access_roles"
down_revision = "20261105_scan_corrections"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "lleida_hacker",
        sa.Column(
            "access_role", sa.String(30), nullable=False, server_default="lleidahacker"
        ),
    )
    # Preserve management access for existing accounts, without silently granting
    # superadmin. Deployment must explicitly bootstrap one trusted superadmin.
    op.execute("UPDATE lleida_hacker SET access_role = 'admin'")
    op.create_check_constraint(
        "ck_staff_access_role",
        "lleida_hacker",
        "access_role IN ('superadmin','admin','lleidahacker')",
    )


def downgrade():
    op.drop_constraint("ck_staff_access_role", "lleida_hacker", type_="check")
    op.drop_column("lleida_hacker", "access_role")
