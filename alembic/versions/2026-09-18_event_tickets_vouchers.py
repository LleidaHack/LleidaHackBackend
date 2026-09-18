"""Check-in tickets (sent QR mail) and physical vouchers per event."""
from alembic import op
import sqlalchemy as sa

revision = "20260918_vouchers"
down_revision = "20260916_sponsors"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "hacker_event_registration",
        sa.Column("ticket_sent_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "event_voucher",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("hacker_id", sa.Integer(), sa.ForeignKey("hacker.user_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("event_id", "hacker_id", name="uq_event_voucher_hacker"),
    )
    op.create_index("ix_event_voucher_id", "event_voucher", ["id"])
    op.create_index("ix_event_voucher_event_id", "event_voucher", ["event_id"])
    op.create_index("ix_event_voucher_code", "event_voucher", ["code"], unique=True)
    op.create_index("ix_event_voucher_hacker_id", "event_voucher", ["hacker_id"])


def downgrade():
    op.drop_index("ix_event_voucher_hacker_id", table_name="event_voucher")
    op.drop_index("ix_event_voucher_code", table_name="event_voucher")
    op.drop_index("ix_event_voucher_event_id", table_name="event_voucher")
    op.drop_index("ix_event_voucher_id", table_name="event_voucher")
    op.drop_table("event_voucher")
    op.drop_column("hacker_event_registration", "ticket_sent_at")
