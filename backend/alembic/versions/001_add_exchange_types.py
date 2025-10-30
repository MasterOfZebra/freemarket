"""Add exchange types support to listing_items

Revision ID: 001_add_exchange_types
Revises: 
Create Date: 2025-01-15 10:00:00.000000

This migration adds support for two exchange types (permanent and temporary):
- exchange_type: VARCHAR, default 'permanent' (PERMANENT | TEMPORARY)
- duration_days: INTEGER, nullable (NULL for permanent, 1-365 for temporary)

All existing items are marked as PERMANENT exchange (backward compatible).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_add_exchange_types'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add exchange type support to listing_items table"""
    
    # Step 1: Add exchange_type column (default PERMANENT for backward compatibility)
    op.add_column(
        'listing_items',
        sa.Column('exchange_type', sa.String(50), nullable=False, server_default='permanent')
    )
    
    # Step 2: Add duration_days column (nullable, for temporary exchange only)
    op.add_column(
        'listing_items',
        sa.Column('duration_days', sa.Integer(), nullable=True)
    )
    
    # Step 3: Create indexes for fast filtering and matching
    op.create_index(
        'ix_listing_exchange_type',
        'listing_items',
        ['listing_id', 'exchange_type'],
        unique=False
    )
    
    op.create_index(
        'ix_category_exchange_type',
        'listing_items',
        ['category', 'exchange_type'],
        unique=False
    )
    
    op.create_index(
        'ix_item_type_category',
        'listing_items',
        ['item_type', 'category'],
        unique=False
    )
    
    op.create_index(
        'ix_created_at_exchange',
        'listing_items',
        ['created_at', 'exchange_type'],
        unique=False
    )
    
    op.create_index(
        'ix_category_value_exchange',
        'listing_items',
        ['category', 'value_tenge', 'exchange_type'],
        unique=False
    )


def downgrade() -> None:
    """Remove exchange type support from listing_items table"""
    
    # Remove indexes
    op.drop_index('ix_category_value_exchange', 'listing_items')
    op.drop_index('ix_created_at_exchange', 'listing_items')
    op.drop_index('ix_item_type_category', 'listing_items')
    op.drop_index('ix_category_exchange_type', 'listing_items')
    op.drop_index('ix_listing_exchange_type', 'listing_items')
    
    # Remove columns
    op.drop_column('listing_items', 'duration_days')
    op.drop_column('listing_items', 'exchange_type')
