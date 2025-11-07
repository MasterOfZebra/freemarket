"""add message delivery tracking fields

Revision ID: i5f8g9h2j7k4
Revises: h4e9b7f5c8a2
Create Date: 2025-11-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i5f8g9h2j7k4'
down_revision: Union[str, Sequence[str], None] = 'h4e9b7f5c8a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add message delivery tracking fields"""

    # Add delivery tracking fields to exchange_messages table
    op.add_column('exchange_messages', sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('exchange_messages', sa.Column('read_at', sa.DateTime(timezone=True), nullable=True))

    # Add indexes for performance
    op.create_index('ix_exchange_messages_delivered_at', 'exchange_messages', ['delivered_at'], unique=False)
    op.create_index('ix_exchange_messages_read_at', 'exchange_messages', ['read_at'], unique=False)


def downgrade() -> None:
    """Remove message delivery tracking fields"""

    # Drop indexes first
    op.drop_index('ix_exchange_messages_read_at', table_name='exchange_messages')
    op.drop_index('ix_exchange_messages_delivered_at', table_name='exchange_messages')

    # Drop columns
    op.drop_column('exchange_messages', 'read_at')
    op.drop_column('exchange_messages', 'delivered_at')
