"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2026-01-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём enum для ролей
    role_enum = sa.Enum('ADMIN', 'MEMBER', name='roleenum')
    role_enum.create(op.get_bind(), checkfirst=True)
    
    # Таблица users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_telegram_user_id'), 'users', ['telegram_user_id'], unique=True)
    
    # Таблица groups
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Таблица group_members
    op.create_table(
        'group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', role_enum, nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_members_group_id'), 'group_members', ['group_id'], unique=False)
    op.create_index(op.f('ix_group_members_user_id'), 'group_members', ['user_id'], unique=False)
    
    # Таблица films
    op.create_table(
        'films',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=50), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('title_original', sa.String(length=500), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('poster_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_films_external_id'), 'films', ['external_id'], unique=False)
    
    # Таблица group_films
    op.create_table(
        'group_films',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('film_id', sa.Integer(), nullable=False),
        sa.Column('added_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['added_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['film_id'], ['films.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_group_films_film_id'), 'group_films', ['film_id'], unique=False)
    op.create_index(op.f('ix_group_films_group_id'), 'group_films', ['group_id'], unique=False)
    
    # Таблица watched
    op.create_table(
        'watched',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_film_id', sa.Integer(), nullable=False),
        sa.Column('watched_at', sa.DateTime(), nullable=False),
        sa.Column('marked_by_user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['group_film_id'], ['group_films.id'], ),
        sa.ForeignKeyConstraint(['marked_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watched_group_film_id'), 'watched', ['group_film_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_watched_group_film_id'), table_name='watched')
    op.drop_table('watched')
    op.drop_index(op.f('ix_group_films_group_id'), table_name='group_films')
    op.drop_index(op.f('ix_group_films_film_id'), table_name='group_films')
    op.drop_table('group_films')
    op.drop_index(op.f('ix_films_external_id'), table_name='films')
    op.drop_table('films')
    op.drop_index(op.f('ix_group_members_user_id'), table_name='group_members')
    op.drop_index(op.f('ix_group_members_group_id'), table_name='group_members')
    op.drop_table('group_members')
    op.drop_table('groups')
    op.drop_index(op.f('ix_users_telegram_user_id'), table_name='users')
    op.drop_table('users')
    
    # Удаляем enum
    sa.Enum(name='roleenum').drop(op.get_bind(), checkfirst=True)
