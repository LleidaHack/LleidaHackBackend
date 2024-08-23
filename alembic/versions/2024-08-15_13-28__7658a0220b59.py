"""empty message

Revision ID: 7658a0220b59
Revises: a19f3a547386
Create Date: 2024-08-15 13:28:38.250607

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7658a0220b59'
down_revision = 'a19f3a547386'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('article_type',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_article_type_name'),
                    'article_type', ['name'],
                    unique=True)
    op.create_table('article', sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(), nullable=True),
                    sa.Column('content', sa.String(), nullable=True),
                    sa.Column('image', sa.String(), nullable=True),
                    sa.Column('creation_date', sa.DateTime(), nullable=True),
                    sa.Column('edition_date', sa.DateTime(), nullable=True),
                    sa.Column('owner_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(
                        ['owner_id'],
                        ['my_user.id'],
                    ), sa.PrimaryKeyConstraint('id'))
    op.create_table(
        'article_article_type',
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('article_type_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['article_id'],
            ['article.id'],
        ), sa.ForeignKeyConstraint(
            ['article_type_id'],
            ['article_type.id'],
        ), sa.PrimaryKeyConstraint('article_id', 'article_type_id'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('article_article_type')
    op.drop_table('article')
    op.drop_index(op.f('ix_article_type_name'), table_name='article_type')
    op.drop_table('article_type')
    # ### end Alembic commands ###