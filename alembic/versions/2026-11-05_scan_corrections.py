"""Keep corrected deliveries while permitting a replacement scan."""

import sqlalchemy as sa

from alembic import op

revision = "20261105_scan_corrections"
down_revision = "20261105_operations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "operation_scan",
        sa.Column("voided", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_constraint(
        "operation_scan_event_id_user_id_kind_target_round_key",
        "operation_scan",
        type_="unique",
    )
    op.create_index(
        "uq_active_operation_scan",
        "operation_scan",
        ["event_id", "user_id", "kind", "target", "round"],
        unique=True,
        postgresql_where=sa.text("NOT voided"),
    )


def downgrade():
    # A corrected row may coexist with its replacement. Refuse destructive loss.
    connection = op.get_bind()
    if connection.execute(
        sa.text("SELECT 1 FROM operation_scan WHERE voided LIMIT 1")
    ).first():
        raise RuntimeError("Cannot downgrade while corrected scans exist")
    op.drop_index("uq_active_operation_scan", table_name="operation_scan")
    op.drop_column("operation_scan", "voided")
    op.create_unique_constraint(
        "operation_scan_event_id_user_id_kind_target_round_key",
        "operation_scan",
        ["event_id", "user_id", "kind", "target", "round"],
    )
