"""empty message

Revision ID: 0bae1f81d197
Revises: e26348b569eb
Create Date: 2023-11-02 13:04:44.518428

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '0bae1f81d197'
down_revision = 'e26348b569eb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('mail_queue', sa.Column('id', sa.Integer(),
                                            nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('subject', sa.String(), nullable=True),
                    sa.Column('body', sa.String(), nullable=True),
                    sa.Column('sent', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['user_id'],
                        ['user.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_mail_queue_body'),
                    'mail_queue', ['body'],
                    unique=False)
    op.create_index(op.f('ix_mail_queue_id'),
                    'mail_queue', ['id'],
                    unique=False)
    op.create_index(op.f('ix_mail_queue_subject'),
                    'mail_queue', ['subject'],
                    unique=False)
    op.alter_column('user',
                    'recive_mails',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user',
                    'recive_mails',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    op.drop_index(op.f('ix_mail_queue_subject'), table_name='mail_queue')
    op.drop_index(op.f('ix_mail_queue_id'), table_name='mail_queue')
    op.drop_index(op.f('ix_mail_queue_body'), table_name='mail_queue')
    op.drop_table('mail_queue')
    # ### end Alembic commands ###
