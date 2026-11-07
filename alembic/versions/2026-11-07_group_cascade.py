"""Delete presentation turns and Devpost links together with their team.

Without ON DELETE CASCADE, deleting a team (or removing its last member) after
enrollment or a Devpost import fails with an IntegrityError (HTTP 500).
"""

from alembic import op

revision = "20261107_group_cascade"
down_revision = "20261106_event_mentors"
branch_labels = None
depends_on = None

FKS = (
    ("event_presentation", "event_presentation_group_id_fkey"),
    ("event_devpost_project", "event_devpost_project_group_id_fkey"),
)


def _recreate(ondelete):
    for table, name in FKS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(
            name, table, "hacker_group", ["group_id"], ["id"], ondelete=ondelete
        )


def upgrade():
    _recreate("CASCADE")


def downgrade():
    _recreate(None)
