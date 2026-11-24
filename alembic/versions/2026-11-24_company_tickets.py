"""Event guests can hold a company ("Empresa") ticket instead of "Convidat"."""

import sqlalchemy as sa

from alembic import op

revision = "20261124_company_tickets"
down_revision = "20261124_event_guests"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_guest",
        sa.Column("kind", sa.String(20), nullable=False, server_default="convidat"),
    )
    op.create_check_constraint(
        "ck_event_guest_kind", "event_guest", "kind IN ('convidat','empresa')"
    )


def downgrade():
    if (
        op.get_bind()
        .execute(
            sa.text("SELECT EXISTS(SELECT 1 FROM event_guest WHERE kind='empresa')")
        )
        .scalar()
    ):
        raise RuntimeError("Export and remove company tickets before downgrading")
    op.drop_constraint("ck_event_guest_kind", "event_guest", type_="check")
    op.drop_column("event_guest", "kind")
