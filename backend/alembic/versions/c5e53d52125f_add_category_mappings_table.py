"""add category_mappings table

Revision ID: c5e53d52125f
Revises: b1552baa1856
Create Date: 2025-11-05 00:06:45.531703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c5e53d52125f'
down_revision: Union[str, Sequence[str], None] = 'b1552baa1856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if exchangetype enum already exists before creating
    conn = op.get_bind()
    result = conn.execute(text("""
    SELECT 1 FROM pg_type WHERE typname = 'exchangetype';
    """))
    
    if not result.fetchone():
        # Only create if it doesn't exist
        conn.execute(text("""
        CREATE TYPE exchangetype AS ENUM ('temporary', 'permanent');
        """))

    # Create category_mappings table
    exchange_type_enum = sa.Enum('temporary', 'permanent', name='exchangetype', create_type=False)
    op.create_table(
        'category_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('legacy_category', sa.String(length=50), nullable=False),
        sa.Column('new_category_slug', sa.String(length=50), nullable=False),
        sa.Column('exchange_type', exchange_type_enum, nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True, default=1.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('legacy_category', 'exchange_type', name='uq_legacy_mapping')
    )
    op.create_index(op.f('ix_category_mappings_id'), 'category_mappings', ['id'], unique=False)
    op.create_index('ix_mapping_exchange_type', 'category_mappings', ['exchange_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop category_mappings table
    op.drop_index('ix_mapping_exchange_type', table_name='category_mappings')
    op.drop_index(op.f('ix_category_mappings_id'), table_name='category_mappings')
    op.drop_table('category_mappings')

    # Drop enum if it exists
    conn = op.get_bind()
    conn.execute(text("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'exchangetype') THEN
            DROP TYPE exchangetype;
        END IF;
    END
    $$;
    """))
