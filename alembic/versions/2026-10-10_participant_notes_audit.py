"""Internal participant notes and registration status audit log."""

import sqlalchemy as sa

from alembic import op

revision = "20261010_notes_audit"
down_revision = "20261010_registered_at"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "event_participant_note",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column(
            "hacker_id", sa.Integer(), sa.ForeignKey("hacker.user_id"), nullable=False
        ),
        sa.Column(
            "author_id", sa.Integer(), sa.ForeignKey("my_user.id"), nullable=True
        ),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_event_participant_note_id", "event_participant_note", ["id"])
    op.create_index(
        "ix_event_participant_note_event_id", "event_participant_note", ["event_id"]
    )
    op.create_index(
        "ix_event_participant_note_hacker_id", "event_participant_note", ["hacker_id"]
    )
    op.create_table(
        "event_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("event.id"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("my_user.id"), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column(
            "target_id", sa.Integer(), sa.ForeignKey("my_user.id"), nullable=True
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_event_audit_log_id", "event_audit_log", ["id"])
    op.create_index("ix_event_audit_log_event_id", "event_audit_log", ["event_id"])


def downgrade():
    op.drop_table("event_audit_log")
    op.drop_table("event_participant_note")
