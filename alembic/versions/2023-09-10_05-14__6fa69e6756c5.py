"""empty message

Revision ID: 6fa69e6756c5
Revises: 91cc228b8be9
Create Date: 2023-09-10 05:14:27.419224

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '6fa69e6756c5'
down_revision = '91cc228b8be9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('hacker_event_rejected',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['event_id'],
                        ['event.id'],
                    ),
                    sa.ForeignKeyConstraint(
                        ['user_id'],
                        ['hacker.user_id'],
                    ), sa.PrimaryKeyConstraint('user_id', 'event_id'))
    op.create_index(op.f('ix_hacker_event_rejected_event_id'),
                    'hacker_event_rejected', ['event_id'],
                    unique=False)
    op.create_index(op.f('ix_hacker_event_rejected_user_id'),
                    'hacker_event_rejected', ['user_id'],
                    unique=False)
    op.add_column('hacker', sa.Column('cv', sa.String(), nullable=True))
    op.add_column('hacker',
                  sa.Column('is_verified', sa.Boolean(), nullable=True))
    op.add_column(
        'hacker', sa.Column('dailyhack_github_repo',
                            sa.String(),
                            nullable=True))
    op.add_column('hacker_event_registration',
                  sa.Column('shirt_size', sa.String(), nullable=True))
    op.add_column('hacker_event_registration',
                  sa.Column('food_restrictions', sa.String(), nullable=True))
    op.add_column('hacker_event_registration',
                  sa.Column('cv', sa.String(), nullable=True))
    op.add_column('hacker_event_registration',
                  sa.Column('description', sa.String(), nullable=True))
    op.add_column('hacker_event_registration',
                  sa.Column('github', sa.String(), nullable=True))
    op.add_column('hacker_event_registration',
                  sa.Column('linkedin', sa.String(), nullable=True))
    op.add_column('user', sa.Column('code', sa.String(), nullable=True))
    op.create_index(op.f('ix_user_code'), 'user', ['code'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_code'), table_name='user')
    op.drop_column('user', 'code')
    op.drop_column('hacker_event_registration', 'linkedin')
    op.drop_column('hacker_event_registration', 'github')
    op.drop_column('hacker_event_registration', 'description')
    op.drop_column('hacker_event_registration', 'cv')
    op.drop_column('hacker_event_registration', 'food_restrictions')
    op.drop_column('hacker_event_registration', 'shirt_size')
    op.drop_column('hacker', 'dailyhack_github_repo')
    op.drop_column('hacker', 'is_verified')
    op.drop_column('hacker', 'cv')
    op.drop_index(op.f('ix_hacker_event_rejected_user_id'),
                  table_name='hacker_event_rejected')
    op.drop_index(op.f('ix_hacker_event_rejected_event_id'),
                  table_name='hacker_event_rejected')
    op.drop_table('hacker_event_rejected')
    # ### end Alembic commands ###
