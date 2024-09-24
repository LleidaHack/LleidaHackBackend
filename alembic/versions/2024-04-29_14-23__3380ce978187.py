"""empty message

Revision ID: 3380ce978187
Revises: 8a4d98b6c642
Create Date: 2024-04-29 14:23:18.829013

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3380ce978187'
down_revision = '8a4d98b6c642'
branch_labels = None
depends_on = None


def upgrade():
    # ### user config change name
    op.alter_column('user_config',
                    'defaultLang',
                    new_column_name='default_lang')
    op.alter_column('user_config',
                    'comercialNotifications',
                    new_column_name='comercial_notifications')
    op.alter_column('user_config',
                    'reciveNotifications',
                    new_column_name='recive_notifications')


def downgrade():
    # ### user config change name##
    op.alter_column('user_config',
                    'default_lang',
                    new_column_name='defaultLang')
    op.alter_column('user_config',
                    'comercial_notifications',
                    new_column_name='comercialNotifications')
    op.alter_column('user_config',
                    'recive_notifications',
                    new_column_name='reciveNotifications')
