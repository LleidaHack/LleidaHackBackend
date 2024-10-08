"""empty message

Revision ID: e3649247c1ec
Revises: 3380ce978187
Create Date: 2024-05-27 01:51:53.081930

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3649247c1ec'
down_revision = '3380ce978187'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_mail_queue_body', table_name='mail_queue')
    op.drop_index('ix_mail_queue_id', table_name='mail_queue')
    op.drop_index('ix_mail_queue_subject', table_name='mail_queue')
    op.drop_table('mail_queue')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'mail_queue',
        sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('subject', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('body', sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column('sent', sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['my_user.id'],
                                name='mail_queue_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='mail_queue_pkey'))
    op.create_index('ix_mail_queue_subject',
                    'mail_queue', ['subject'],
                    unique=False)
    op.create_index('ix_mail_queue_id', 'mail_queue', ['id'], unique=False)
    op.create_index('ix_mail_queue_body', 'mail_queue', ['body'], unique=False)
    # ### end Alembic commands ###
