"""Record the team’s Josep Maria Ribó prize choice."""

from alembic import op
import sqlalchemy as sa

revision = "20261117_ribo_prize"
down_revision = "20261117_devpost_materials"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "event_challenge_vote",
        sa.Column(
            "ribo_prize", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )


def downgrade():
    op.drop_column("event_challenge_vote", "ribo_prize")
