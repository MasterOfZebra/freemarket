"""add match_index table for incremental matching

Revision ID: f2a5c8e9d1b3
Revises: ecee305c0829
Create Date: 2025-11-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2a5c8e9d1b3'
down_revision: Union[str, Sequence[str], None] = 'ecee305c0829'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create match_index table for incremental matching optimization."""

    # Create match_index table
    op.create_table(
        'match_index',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=10), nullable=False),  # 'want' | 'offer'
        sa.Column('exchange_type', sa.String(length=20), nullable=False),  # 'PERMANENT' | 'TEMPORARY'
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('tags', postgresql.JSONB(), nullable=True),  # Array of tags for advanced filtering
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes for performance
    op.create_index('ix_match_index_user_id', 'match_index', ['user_id'], unique=False)
    op.create_index('ix_match_index_category', 'match_index', ['category'], unique=False)
    op.create_index('ix_match_index_exchange_type', 'match_index', ['exchange_type'], unique=False)
    op.create_index('ix_match_index_item_type', 'match_index', ['item_type'], unique=False)
    op.create_index('ix_match_index_updated_at', 'match_index', ['updated_at'], unique=False)

    # Composite index for quick lookups
    op.create_index('ix_match_index_category_user', 'match_index', ['category', 'user_id'], unique=False)

    # GIN index for tags array (PostgreSQL specific)
    op.execute('CREATE INDEX ix_match_index_tags_gin ON match_index USING GIN (tags jsonb_ops)')

    # Unique constraint to prevent duplicates
    op.create_unique_constraint('uq_match_index_user_category_type', 'match_index',
                               ['user_id', 'category', 'item_type', 'exchange_type'])

    # Add is_archived column to listing_items for soft delete after exchange
    op.add_column('listing_items', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_listing_items_archived', 'listing_items', ['is_archived'], unique=False)


def downgrade() -> None:
    """Drop match_index table and related indexes."""

    # Drop indexes first
    op.drop_index('ix_match_index_tags_gin', table_name='match_index')
    op.drop_index('ix_match_index_category_user', table_name='match_index')
    op.drop_index('ix_match_index_updated_at', table_name='match_index')
    op.drop_index('ix_match_index_item_type', table_name='match_index')
    op.drop_index('ix_match_index_exchange_type', table_name='match_index')
    op.drop_index('ix_match_index_category', table_name='match_index')
    op.drop_index('ix_match_index_user_id', table_name='match_index')

    # Drop constraint
    op.drop_constraint('uq_match_index_user_category_type', 'match_index', type_='unique')

    # Drop table
    op.drop_table('match_index')

    # Remove is_archived column
    op.drop_index('ix_listing_items_archived', table_name='listing_items')
    op.drop_column('listing_items', 'is_archived')
