"""Record explicit MLH code of conduct acceptance on user configuration."""

import sqlalchemy as sa

from alembic import op

revision = "20261121_mlh_consent"
down_revision = "20261117_pending_devpost"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_config",
        sa.Column(
            "mlh_code_of_conduct", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )


def downgrade():
    op.drop_column("user_config", "mlh_code_of_conduct")
