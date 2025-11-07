"""add notifications tables for user events and reviews

Revision ID: h4e9b7f5c8a2
Revises: g3c9f2e8a4d7
Create Date: 2025-11-08 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h4e9b7f5c8a2'
down_revision: Union[str, Sequence[str], None] = 'g3c9f2e8a4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications and reviews tables."""

    # Create user_events table for notifications
    op.create_table(
        'user_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),  # MessageReceived, OfferMatched, etc.
        sa.Column('related_id', sa.Integer(), nullable=True),  # ID of related object (exchange, listing, etc.)
        sa.Column('payload', sa.JSON(), nullable=True),  # Additional event data
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_reviews table for ratings
    op.create_table(
        'user_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),  # Who left the review
        sa.Column('target_id', sa.Integer(), nullable=False),  # Who received the review
        sa.Column('exchange_id', sa.String(length=100), nullable=False),  # Related exchange
        sa.Column('rating', sa.Integer(), nullable=False),  # 1-5 stars
        sa.Column('text', sa.Text(), nullable=True),  # Review text
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create exchange_history table for tracking exchange lifecycle
    op.create_table(
        'exchange_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),  # created, confirmed, completed, cancelled
        sa.Column('user_id', sa.Integer(), nullable=True),  # User who triggered the event
        sa.Column('details', sa.JSON(), nullable=True),  # Additional event data
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for performance
    # User events
    op.create_index('ix_user_events_user_id', 'user_events', ['user_id'], unique=False)
    op.create_index('ix_user_events_event_type', 'user_events', ['event_type'], unique=False)
    op.create_index('ix_user_events_is_read', 'user_events', ['is_read'], unique=False)
    op.create_index('ix_user_events_created_at', 'user_events', ['created_at'], unique=False)
    op.create_index('ix_user_events_user_read', 'user_events', ['user_id', 'is_read'], unique=False)

    # User reviews
    op.create_index('ix_user_reviews_author_id', 'user_reviews', ['author_id'], unique=False)
    op.create_index('ix_user_reviews_target_id', 'user_reviews', ['target_id'], unique=False)
    op.create_index('ix_user_reviews_exchange_id', 'user_reviews', ['exchange_id'], unique=False)
    op.create_index('ix_user_reviews_rating', 'user_reviews', ['rating'], unique=False)
    op.create_index('ix_user_reviews_created_at', 'user_reviews', ['created_at'], unique=False)

    # Exchange history
    op.create_index('ix_exchange_history_exchange_id', 'exchange_history', ['exchange_id'], unique=False)
    op.create_index('ix_exchange_history_event_type', 'exchange_history', ['event_type'], unique=False)
    op.create_index('ix_exchange_history_created_at', 'exchange_history', ['created_at'], unique=False)

    # Add rating cache columns to users table
    op.add_column('users', sa.Column('rating_avg', sa.Float(), nullable=True, default=0.0))
    op.add_column('users', sa.Column('rating_count', sa.Integer(), nullable=False, default=0))
    op.add_column('users', sa.Column('last_rating_update', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Drop notifications and reviews tables."""

    # Remove rating cache columns
    op.drop_column('users', 'last_rating_update')
    op.drop_column('users', 'rating_count')
    op.drop_column('users', 'rating_avg')

    # Drop indexes
    op.drop_index('ix_exchange_history_created_at', table_name='exchange_history')
    op.drop_index('ix_exchange_history_event_type', table_name='exchange_history')
    op.drop_index('ix_exchange_history_exchange_id', table_name='exchange_history')

    op.drop_index('ix_user_reviews_created_at', table_name='user_reviews')
    op.drop_index('ix_user_reviews_rating', table_name='user_reviews')
    op.drop_index('ix_user_reviews_exchange_id', table_name='user_reviews')
    op.drop_index('ix_user_reviews_target_id', table_name='user_reviews')
    op.drop_index('ix_user_reviews_author_id', table_name='user_reviews')

    op.drop_index('ix_user_events_user_read', table_name='user_events')
    op.drop_index('ix_user_events_created_at', table_name='user_events')
    op.drop_index('ix_user_events_is_read', table_name='user_events')
    op.drop_index('ix_user_events_event_type', table_name='user_events')
    op.drop_index('ix_user_events_user_id', table_name='user_events')

    # Drop tables
    op.drop_table('exchange_history')
    op.drop_table('user_reviews')
    op.drop_table('user_events')
