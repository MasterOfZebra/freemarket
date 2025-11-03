"""create users table for authentication

Revision ID: cf5a32f4e1d5
Revises: cbfc66708806
Create Date: 2025-11-03 21:36:12.393326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf5a32f4e1d5'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users table for authentication."""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('full_name', sa.String(length=100), nullable=True),
        sa.Column('telegram_contact', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=50), server_default='Алматы', nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('trust_score', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('exchange_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('rating_avg', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('phone_verified', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contact', sa.JSON(), nullable=True),
        sa.Column('locations', sa.ARRAY(sa.String()), server_default='{"Алматы"}', nullable=True),
        sa.Column('telegram_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)


def downgrade() -> None:
    """Drop users table."""
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
