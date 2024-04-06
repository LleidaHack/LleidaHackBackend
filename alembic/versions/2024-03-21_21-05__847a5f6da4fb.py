"""empty message

Revision ID: 847a5f6da4fb
Revises: beb25bc83663
Create Date: 2024-03-21 21:05:33.884669

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '847a5f6da4fb'
down_revision = 'beb25bc83663'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('uq_my_user_code', 'my_user', ['code'])

    op.execute(
        'ALTER TABLE company_user ALTER COLUMN active TYPE boolean USING active::boolean'
    )
    op.execute(
        'ALTER TABLE lleida_hacker ALTER COLUMN active TYPE boolean USING active::boolean'
    )
    op.execute(
        'ALTER TABLE hacker ALTER COLUMN banned TYPE boolean USING banned::boolean'
    )
    op.drop_column('event', 'status')
    op.drop_column('lleida_hacker', 'rejected')
    op.drop_column('my_user', 'recive_mails')
    op.drop_column('my_user', 'lleidacoins_claimed')
    op.drop_column('my_user', 'is_image_url')

    op.drop_table('user_geocaching')
    op.drop_table('geocaching')

    op.drop_index('ix_user_code', table_name='my_user')
    op.drop_index('ix_user_email', table_name='my_user')
    op.drop_index('ix_user_id', table_name='my_user')
    op.drop_index('ix_user_nickname', table_name='my_user')
    op.drop_index('ix_user_telephone', table_name='my_user')
    op.create_index(op.f('ix_my_user_code'), 'my_user', ['code'], unique=True)
    op.create_index(op.f('ix_my_user_email'),
                    'my_user', ['email'],
                    unique=True)
    op.create_index(op.f('ix_my_user_id'), 'my_user', ['id'], unique=False)
    op.create_index(op.f('ix_my_user_nickname'),
                    'my_user', ['nickname'],
                    unique=True)
    op.create_index(op.f('ix_my_user_telephone'),
                    'my_user', ['telephone'],
                    unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'my_user',
        sa.Column('is_image_url',
                  sa.BOOLEAN(),
                  autoincrement=False,
                  nullable=True))
    op.add_column(
        'my_user',
        sa.Column('lleidacoins_claimed',
                  sa.BOOLEAN(),
                  autoincrement=False,
                  nullable=True))
    op.add_column(
        'my_user',
        sa.Column('recive_mails',
                  sa.BOOLEAN(),
                  autoincrement=False,
                  nullable=True))
    op.add_column(
        'lleida_hacker',
        sa.Column('rejected', sa.INTEGER(), autoincrement=False,
                  nullable=True))
    op.add_column(
        'event',
        sa.Column('status', sa.INTEGER(), autoincrement=False, nullable=True))

    op.execute(
        'ALTER TABLE company_user ALTER COLUMN active TYPE INT USING active::integer'
    )
    op.execute(
        'ALTER TABLE lleida_hacker ALTER COLUMN active TYPE INT USING active::integer'
    )
    op.execute(
        'ALTER TABLE hacker ALTER COLUMN banned TYPE INT USING banned::integer'
    )
    # ### end Alembic commands ###
    op.create_table('geocaching', sa.Column('code',
                                            sa.String(),
                                            nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('code'))
    op.create_index(op.f('ix_geocaching_code'),
                    'geocaching', ['code'],
                    unique=False)
    op.create_table('user_geocaching',
                    sa.Column('user_code', sa.String(), nullable=False),
                    sa.Column('code', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['code'],
                        ['geocaching.code'],
                    ),
                    sa.ForeignKeyConstraint(
                        ['user_code'],
                        ['my_user.code'],
                    ), sa.PrimaryKeyConstraint('user_code', 'code'))
