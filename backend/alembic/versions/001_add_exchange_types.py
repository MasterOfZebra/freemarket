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
down_revision = 'ecee305c0829'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Exchange types already added in base table creation - no action needed."""
    pass


def downgrade() -> None:
    """Exchange types are part of base table - no downgrade needed."""
    pass
