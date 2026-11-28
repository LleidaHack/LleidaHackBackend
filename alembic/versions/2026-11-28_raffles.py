"""Public HackEPS raffles and their private entries."""

import sqlalchemy as sa

from alembic import op

revision = "20261128_raffles"
down_revision = "20261124_company_tickets"
branch_labels = None
depends_on = None


def upgrade():
    raffles = op.create_table(
        "raffle",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("theme", sa.String(16), nullable=False, server_default="hackeps"),
        sa.Column("drawn_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        raffles,
        [
            {"name": "Sorteig JCA", "theme": "cinema"},
            {"name": "Sorteig Cafès Batalla", "theme": "coffee"},
        ],
    )
    op.create_table(
        "raffle_entry",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("raffle_id", sa.Integer, sa.ForeignKey("raffle.id"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("phone", sa.String(16), nullable=False),
        sa.Column("postal_code", sa.String(5), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("winner_position", sa.Integer),
        sa.UniqueConstraint("raffle_id", "email"),
        sa.UniqueConstraint("raffle_id", "winner_position"),
    )


def downgrade():
    op.drop_table("raffle_entry")
    op.drop_table("raffle")
