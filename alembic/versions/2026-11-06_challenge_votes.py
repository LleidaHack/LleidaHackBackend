"""One preliminary challenge choice per event team."""

import sqlalchemy as sa

from alembic import op

revision = "20261106_challenge_votes"
down_revision = "20261106_devpost"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_challenge_vote",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column(
            "group_id",
            sa.Integer(),
            sa.ForeignKey("hacker_group.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("challenge", sa.String(80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("event_id", "group_id"),
    )
    op.create_index(
        "ix_event_challenge_vote_event_id", "event_challenge_vote", ["event_id"]
    )


def downgrade():
    op.drop_table("event_challenge_vote")
