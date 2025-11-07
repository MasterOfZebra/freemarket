"""add exchange_messages table for chat functionality

Revision ID: g3c9f2e8a4d7
Revises: f2a5c8e9d1b3
Create Date: 2025-11-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g3c9f2e8a4d7'
down_revision: Union[str, Sequence[str], None] = 'f2a5c8e9d1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create exchange_messages table for chat functionality."""

    # Create exchange_messages table
    op.create_table(
        'exchange_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('exchange_id', sa.String(length=100), nullable=False),  # Format: mutual_X_Y_A_B
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False, server_default='text'),  # text, image, system
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for performance
    op.create_index('ix_exchange_messages_exchange_id', 'exchange_messages', ['exchange_id'], unique=False)
    op.create_index('ix_exchange_messages_sender_id', 'exchange_messages', ['sender_id'], unique=False)
    op.create_index('ix_exchange_messages_created_at', 'exchange_messages', ['created_at'], unique=False)
    op.create_index('ix_exchange_messages_is_read', 'exchange_messages', ['is_read'], unique=False)

    # Composite index for chat queries (exchange + time)
    op.create_index('ix_exchange_messages_chat', 'exchange_messages', ['exchange_id', 'created_at'], unique=False)

    # Composite index for unread messages per user
    op.create_index('ix_exchange_messages_unread', 'exchange_messages', ['exchange_id', 'is_read'], unique=False)


def downgrade() -> None:
    """Drop exchange_messages table and related indexes."""

    # Drop indexes first
    op.drop_index('ix_exchange_messages_unread', table_name='exchange_messages')
    op.drop_index('ix_exchange_messages_chat', table_name='exchange_messages')
    op.drop_index('ix_exchange_messages_is_read', table_name='exchange_messages')
    op.drop_index('ix_exchange_messages_created_at', table_name='exchange_messages')
    op.drop_index('ix_exchange_messages_sender_id', table_name='exchange_messages')
    op.drop_index('ix_exchange_messages_exchange_id', table_name='exchange_messages')

    # Drop table
    op.drop_table('exchange_messages')
