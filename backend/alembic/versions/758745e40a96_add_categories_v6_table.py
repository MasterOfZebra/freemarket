"""add categories_v6 table

Revision ID: 758745e40a96
Revises: c5e53d52125f
Create Date: 2025-11-05 00:08:24.778679

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '758745e40a96'
down_revision: Union[str, Sequence[str], None] = 'c5e53d52125f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create categories_v6 table with VARCHAR instead of enum to avoid conflicts
    # Data will be inserted via raw SQL in init script, so enum is not needed
    op.create_table(
        'categories_v6',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('group', sa.String(length=100), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=False),
        sa.Column('exchange_type', sa.String(length=20), nullable=False),  # VARCHAR instead of enum
        sa.Column('form_schema', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['version_id'], ['category_versions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version_id', 'exchange_type', 'slug', name='uq_category_version_exchange_slug')
    )
    op.create_index(op.f('ix_categories_v6_id'), 'categories_v6', ['id'], unique=False)
    op.create_index(op.f('ix_categories_v6_slug'), 'categories_v6', ['slug'], unique=False)
    op.create_index(op.f('ix_categories_v6_exchange_type'), 'categories_v6', ['exchange_type'], unique=False)
    op.create_index('ix_category_active_version', 'categories_v6', ['version_id', 'is_active', 'exchange_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop categories_v6 table
    op.drop_index('ix_category_active_version', table_name='categories_v6')
    op.drop_index(op.f('ix_categories_v6_exchange_type'), table_name='categories_v6')
    op.drop_index(op.f('ix_categories_v6_slug'), table_name='categories_v6')
    op.drop_index(op.f('ix_categories_v6_id'), table_name='categories_v6')
    op.drop_table('categories_v6')
