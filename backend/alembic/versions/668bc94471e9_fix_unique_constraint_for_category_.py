"""fix unique constraint for category_mappings

Revision ID: 668bc94471e9
Revises: 758745e40a96
Create Date: 2025-11-05 14:17:28.083358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '668bc94471e9'
down_revision: Union[str, Sequence[str], None] = '758745e40a96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove the old unique constraint (legacy_category, exchange_type)
    op.drop_constraint('uq_legacy_mapping', 'category_mappings', type_='unique')

    # Create new unique constraint (legacy_category, new_category_slug, exchange_type)
    op.create_unique_constraint(
        'uq_legacy_mapping_full',
        'category_mappings',
        ['legacy_category', 'new_category_slug', 'exchange_type']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the new unique constraint
    op.drop_constraint('uq_legacy_mapping_full', 'category_mappings', type_='unique')

    # Restore the old unique constraint
    op.create_unique_constraint(
        'uq_legacy_mapping',
        'category_mappings',
        ['legacy_category', 'exchange_type']
    )
