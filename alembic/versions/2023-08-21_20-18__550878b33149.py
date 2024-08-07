"""empty message

Revision ID: 550878b33149
Revises: 
Create Date: 2023-08-21 20:18:05.923755

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '550878b33149'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('event', sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('start_date', sa.DateTime(), nullable=True),
                    sa.Column('end_date', sa.DateTime(), nullable=True),
                    sa.Column('location', sa.String(), nullable=True),
                    sa.Column('archived', sa.Boolean(), nullable=True),
                    sa.Column('status', sa.Integer(), nullable=True),
                    sa.Column('price', sa.Integer(), nullable=True),
                    sa.Column('max_participants', sa.Integer(), nullable=True),
                    sa.Column('max_sponsors', sa.Integer(), nullable=True),
                    sa.Column('image', sa.String(), nullable=True),
                    sa.Column('is_image_url', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_event_id'), 'event', ['id'], unique=False)
    op.create_table(
        'role', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name',
                  sa.Enum('Admin', 'User', 'Guest', name='roleenum'),
                  nullable=True), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_role_id'), 'role', ['id'], unique=False)
    op.create_index(op.f('ix_role_name'), 'role', ['name'], unique=False)
    op.create_table('user', sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('nickname', sa.String(), nullable=True),
                    sa.Column('password', sa.String(), nullable=True),
                    sa.Column('birthdate', sa.DateTime(), nullable=True),
                    sa.Column('food_restrictions', sa.String(), nullable=True),
                    sa.Column('email', sa.String(), nullable=True),
                    sa.Column('telephone', sa.String(), nullable=True),
                    sa.Column('address', sa.String(), nullable=True),
                    sa.Column('shirt_size', sa.String(), nullable=True),
                    sa.Column('type', sa.String(), nullable=True),
                    sa.Column('image', sa.String(), nullable=True),
                    sa.Column('is_image_url', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email'))
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_table('company', sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('address', sa.String(), nullable=True),
                    sa.Column('telephone', sa.String(), nullable=True),
                    sa.Column('website', sa.String(), nullable=True),
                    sa.Column('image', sa.String(), nullable=True),
                    sa.Column('is_image_url', sa.Boolean(), nullable=True),
                    sa.Column('linkdin', sa.String(), nullable=True),
                    sa.Column('leader_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['leader_id'],
                        ['user.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_company_id'), 'company', ['id'], unique=False)
    op.create_table('hacker', sa.Column('user_id',
                                        sa.Integer(),
                                        nullable=False),
                    sa.Column('banned', sa.Integer(), nullable=True),
                    sa.Column('github', sa.String(), nullable=True),
                    sa.Column('linkedin', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['user_id'],
                        ['user.id'],
                    ), sa.PrimaryKeyConstraint('user_id'))
    op.create_table('lleida_hacker',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('role', sa.String(), nullable=True),
                    sa.Column('nif', sa.String(), nullable=True),
                    sa.Column('student', sa.Boolean(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=True),
                    sa.Column('github', sa.String(), nullable=True),
                    sa.Column('logo', sa.String(), nullable=True),
                    sa.Column('accepted', sa.Boolean(), nullable=True),
                    sa.Column('rejected', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['user_id'],
                        ['user.id'],
                    ), sa.PrimaryKeyConstraint('user_id'),
                    sa.UniqueConstraint('nif'))
    op.create_table('meal', sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['event_id'],
                        ['event.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_meal_event_id'),
                    'meal', ['event_id'],
                    unique=False)
    op.create_index(op.f('ix_meal_id'), 'meal', ['id'], unique=False)
    op.create_table('notification',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=True),
                    sa.Column('message', sa.String(), nullable=True),
                    sa.Column('read', sa.Boolean(), nullable=True),
                    sa.Column('created_at', sa.String(), nullable=True),
                    sa.Column('updated_at', sa.String(), nullable=True),
                    sa.Column('deleted_at', sa.String(), nullable=True),
                    sa.Column('is_mail', sa.Boolean(), nullable=True),
                    sa.Column('deleted', sa.Boolean(), nullable=True),
                    sa.Column('type', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['user_id'],
                        ['user.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_notification_id'),
                    'notification', ['id'],
                    unique=False)
    op.create_table('company_event_participation',
                    sa.Column('company_id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['company_id'],
                        ['company.id'],
                    ), sa.ForeignKeyConstraint(
                        ['event_id'],
                        ['event.id'],
                    ), sa.PrimaryKeyConstraint('company_id', 'event_id'))
    op.create_index(op.f('ix_company_event_participation_company_id'),
                    'company_event_participation', ['company_id'],
                    unique=False)
    op.create_index(op.f('ix_company_event_participation_event_id'),
                    'company_event_participation', ['event_id'],
                    unique=False)
    op.create_table('company_user',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('company_id', sa.Integer(), nullable=False),
                    sa.Column('active', sa.Integer(), nullable=True),
                    sa.Column('role', sa.String(), nullable=True),
                    sa.Column('accepted', sa.Boolean(), nullable=True),
                    sa.Column('rejected', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['company_id'],
                        ['company.id'],
                    ), sa.ForeignKeyConstraint(
                        ['user_id'],
                        ['user.id'],
                    ), sa.PrimaryKeyConstraint('user_id', 'company_id'))
    op.create_table('hacker_accepted_notification',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['event_id'],
                        ['event.id'],
                    ), sa.ForeignKeyConstraint(
                        ['id'],
                        ['notification.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_hacker_accepted_notification_id'),
                    'hacker_accepted_notification', ['id'],
                    unique=False)
    op.create_table('hacker_event_accepted',
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
    op.create_index(op.f('ix_hacker_event_accepted_event_id'),
                    'hacker_event_accepted', ['event_id'],
                    unique=False)
    op.create_index(op.f('ix_hacker_event_accepted_user_id'),
                    'hacker_event_accepted', ['user_id'],
                    unique=False)
    op.create_table('hacker_event_participation',
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
    op.create_index(op.f('ix_hacker_event_participation_event_id'),
                    'hacker_event_participation', ['event_id'],
                    unique=False)
    op.create_index(op.f('ix_hacker_event_participation_user_id'),
                    'hacker_event_participation', ['user_id'],
                    unique=False)
    op.create_table('hacker_event_registration',
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
    op.create_index(op.f('ix_hacker_event_registration_event_id'),
                    'hacker_event_registration', ['event_id'],
                    unique=False)
    op.create_index(op.f('ix_hacker_event_registration_user_id'),
                    'hacker_event_registration', ['user_id'],
                    unique=False)
    op.create_table(
        'hacker_group', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('leader_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['event_id'],
            ['event.id'],
        ), sa.ForeignKeyConstraint(
            ['leader_id'],
            ['hacker.user_id'],
        ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_hacker_group_code'),
                    'hacker_group', ['code'],
                    unique=True)
    op.create_index(op.f('ix_hacker_group_id'),
                    'hacker_group', ['id'],
                    unique=False)
    op.create_table('hacker_meal',
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('meal_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['meal_id'],
                        ['meal.id'],
                    ),
                    sa.ForeignKeyConstraint(
                        ['user_id'],
                        ['hacker.user_id'],
                    ), sa.PrimaryKeyConstraint('user_id', 'meal_id'))
    op.create_index(op.f('ix_hacker_meal_meal_id'),
                    'hacker_meal', ['meal_id'],
                    unique=False)
    op.create_index(op.f('ix_hacker_meal_user_id'),
                    'hacker_meal', ['user_id'],
                    unique=False)
    op.create_table('hacker_rejected_notification',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('event_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['event_id'],
                        ['event.id'],
                    ), sa.ForeignKeyConstraint(
                        ['id'],
                        ['notification.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_hacker_rejected_notification_id'),
                    'hacker_rejected_notification', ['id'],
                    unique=False)
    op.create_table('lleida_hacker_accepted_notification',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['id'],
                        ['notification.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_lleida_hacker_accepted_notification_id'),
                    'lleida_hacker_accepted_notification', ['id'],
                    unique=False)
    op.create_table(
        'lleida_hacker_event_participation',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['event_id'],
            ['event.id'],
        ), sa.ForeignKeyConstraint(
            ['user_id'],
            ['lleida_hacker.user_id'],
        ), sa.PrimaryKeyConstraint('user_id', 'event_id'))
    op.create_index(op.f('ix_lleida_hacker_event_participation_event_id'),
                    'lleida_hacker_event_participation', ['event_id'],
                    unique=False)
    op.create_index(op.f('ix_lleida_hacker_event_participation_user_id'),
                    'lleida_hacker_event_participation', ['user_id'],
                    unique=False)
    op.create_table(
        'lleida_hacker_group', sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('leader_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['leader_id'],
            ['lleida_hacker.user_id'],
        ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_lleida_hacker_group_id'),
                    'lleida_hacker_group', ['id'],
                    unique=False)
    op.create_table('lleida_hacker_rejected_notification',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['id'],
                        ['notification.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_lleida_hacker_rejected_notification_id'),
                    'lleida_hacker_rejected_notification', ['id'],
                    unique=False)
    op.create_table(
        'hacker_group_user',
        sa.Column('hacker_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['group_id'],
            ['hacker_group.id'],
        ), sa.ForeignKeyConstraint(
            ['hacker_id'],
            ['hacker.user_id'],
        ), sa.PrimaryKeyConstraint('hacker_id', 'group_id'))
    op.create_table(
        'lleida_hacker_group_user',
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['group_id'],
            ['lleida_hacker_group.id'],
        ), sa.ForeignKeyConstraint(
            ['user_id'],
            ['lleida_hacker.user_id'],
        ), sa.PrimaryKeyConstraint('group_id', 'user_id'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('lleida_hacker_group_user')
    op.drop_table('hacker_group_user')
    op.drop_index(op.f('ix_lleida_hacker_rejected_notification_id'),
                  table_name='lleida_hacker_rejected_notification')
    op.drop_table('lleida_hacker_rejected_notification')
    op.drop_index(op.f('ix_lleida_hacker_group_id'),
                  table_name='lleida_hacker_group')
    op.drop_table('lleida_hacker_group')
    op.drop_index(op.f('ix_lleida_hacker_event_participation_user_id'),
                  table_name='lleida_hacker_event_participation')
    op.drop_index(op.f('ix_lleida_hacker_event_participation_event_id'),
                  table_name='lleida_hacker_event_participation')
    op.drop_table('lleida_hacker_event_participation')
    op.drop_index(op.f('ix_lleida_hacker_accepted_notification_id'),
                  table_name='lleida_hacker_accepted_notification')
    op.drop_table('lleida_hacker_accepted_notification')
    op.drop_index(op.f('ix_hacker_rejected_notification_id'),
                  table_name='hacker_rejected_notification')
    op.drop_table('hacker_rejected_notification')
    op.drop_index(op.f('ix_hacker_meal_user_id'), table_name='hacker_meal')
    op.drop_index(op.f('ix_hacker_meal_meal_id'), table_name='hacker_meal')
    op.drop_table('hacker_meal')
    op.drop_index(op.f('ix_hacker_group_id'), table_name='hacker_group')
    op.drop_index(op.f('ix_hacker_group_code'), table_name='hacker_group')
    op.drop_table('hacker_group')
    op.drop_index(op.f('ix_hacker_event_registration_user_id'),
                  table_name='hacker_event_registration')
    op.drop_index(op.f('ix_hacker_event_registration_event_id'),
                  table_name='hacker_event_registration')
    op.drop_table('hacker_event_registration')
    op.drop_index(op.f('ix_hacker_event_participation_user_id'),
                  table_name='hacker_event_participation')
    op.drop_index(op.f('ix_hacker_event_participation_event_id'),
                  table_name='hacker_event_participation')
    op.drop_table('hacker_event_participation')
    op.drop_index(op.f('ix_hacker_event_accepted_user_id'),
                  table_name='hacker_event_accepted')
    op.drop_index(op.f('ix_hacker_event_accepted_event_id'),
                  table_name='hacker_event_accepted')
    op.drop_table('hacker_event_accepted')
    op.drop_index(op.f('ix_hacker_accepted_notification_id'),
                  table_name='hacker_accepted_notification')
    op.drop_table('hacker_accepted_notification')
    op.drop_table('company_user')
    op.drop_index(op.f('ix_company_event_participation_event_id'),
                  table_name='company_event_participation')
    op.drop_index(op.f('ix_company_event_participation_company_id'),
                  table_name='company_event_participation')
    op.drop_table('company_event_participation')
    op.drop_index(op.f('ix_notification_id'), table_name='notification')
    op.drop_table('notification')
    op.drop_index(op.f('ix_meal_id'), table_name='meal')
    op.drop_index(op.f('ix_meal_event_id'), table_name='meal')
    op.drop_table('meal')
    op.drop_table('lleida_hacker')
    op.drop_table('hacker')
    op.drop_index(op.f('ix_company_id'), table_name='company')
    op.drop_table('company')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_role_name'), table_name='role')
    op.drop_index(op.f('ix_role_id'), table_name='role')
    op.drop_table('role')
    op.drop_index(op.f('ix_event_id'), table_name='event')
    op.drop_table('event')
    op.execute('DROP TYPE roleenum cascade;')
    # ### end Alembic commands ###
