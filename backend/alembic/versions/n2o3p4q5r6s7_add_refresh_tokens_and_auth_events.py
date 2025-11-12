"""add refresh_tokens and auth_events tables for JWT authentication

Revision ID: n2o3p4q5r6s7
Revises: m1n2o3p4q5r6
Create Date: 2025-11-11 21:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'n2o3p4q5r6s7'
down_revision: Union[str, None] = 'm1n2o3p4q5r6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create refresh_tokens and auth_events tables."""
    # Create refresh_tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('device_id', sa.String(length=64), nullable=False),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_reason', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('ix_refresh_tokens_id', 'refresh_tokens', ['id'], unique=False)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], unique=False)
    op.create_index('ix_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index('ix_refresh_tokens_is_revoked', 'refresh_tokens', ['is_revoked'], unique=False)
    op.create_index('ix_refresh_user_device', 'refresh_tokens', ['user_id', 'device_id'], unique=False)
    op.create_index('ix_refresh_expires', 'refresh_tokens', ['expires_at', 'is_revoked'], unique=False)

    # Create auth_events table
    op.create_table(
        'auth_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('device_id', sa.String(length=64), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index('ix_auth_events_id', 'auth_events', ['id'], unique=False)
    op.create_index('ix_auth_events_user_id', 'auth_events', ['user_id'], unique=False)
    op.create_index('ix_auth_user_time', 'auth_events', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_auth_event_type', 'auth_events', ['event_type', 'created_at'], unique=False)


def downgrade() -> None:
    """Drop refresh_tokens and auth_events tables."""
    op.drop_index('ix_auth_event_type', table_name='auth_events')
    op.drop_index('ix_auth_user_time', table_name='auth_events')
    op.drop_index('ix_auth_events_user_id', table_name='auth_events')
    op.drop_index('ix_auth_events_id', table_name='auth_events')
    op.drop_table('auth_events')

    op.drop_index('ix_refresh_expires', table_name='refresh_tokens')
    op.drop_index('ix_refresh_user_device', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_is_revoked', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_expires_at', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_index('ix_refresh_tokens_id', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

