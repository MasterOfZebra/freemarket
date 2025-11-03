"""create base listing_items table

Revision ID: ecee305c0829
Revises: cbfc66708806
Create Date: 2025-11-03 22:16:50.180542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ecee305c0829'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create base listing_items table with all columns."""
    op.create_table(
        'listing_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('listing_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=10), nullable=False),  # want | offer
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('exchange_type', sa.String(length=20), nullable=False, server_default='permanent'),
        sa.Column('item_name', sa.String(length=100), nullable=False),
        sa.Column('value_tenge', sa.Integer(), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_listing_exchange_type', 'listing_items', ['listing_id', 'exchange_type'], unique=False)
    op.create_index('ix_category_exchange_type', 'listing_items', ['category', 'exchange_type'], unique=False)
    op.create_index('ix_item_type_category', 'listing_items', ['item_type', 'category'], unique=False)
    op.create_index('ix_created_at_exchange', 'listing_items', ['created_at', 'exchange_type'], unique=False)
    op.create_index('ix_category_value_exchange', 'listing_items', ['category', 'value_tenge', 'exchange_type'], unique=False)
    op.create_index(op.f('ix_listing_items_id'), 'listing_items', ['id'], unique=False)
    op.create_index(op.f('ix_listing_items_listing_id'), 'listing_items', ['listing_id'], unique=False)


def downgrade() -> None:
    """Drop listing_items table."""
    op.drop_index(op.f('ix_listing_items_listing_id'), table_name='listing_items')
    op.drop_index(op.f('ix_listing_items_id'), table_name='listing_items')
    op.drop_index('ix_category_value_exchange', table_name='listing_items')
    op.drop_index('ix_created_at_exchange', table_name='listing_items')
    op.drop_index('ix_item_type_category', table_name='listing_items')
    op.drop_index('ix_category_exchange_type', table_name='listing_items')
    op.drop_index('ix_listing_exchange_type', table_name='listing_items')
    op.drop_table('listing_items')
