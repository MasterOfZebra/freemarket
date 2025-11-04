"""add category_versions table

Revision ID: b1552baa1856
Revises: cbfc66708806
Create Date: 2025-11-05 00:05:25.225774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1552baa1856'
down_revision: Union[str, Sequence[str], None] = 'cbfc66708806'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create category_versions table
    op.create_table(
        'category_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version')
    )
    op.create_index(op.f('ix_category_versions_id'), 'category_versions', ['id'], unique=False)
    op.create_index(op.f('ix_category_versions_version'), 'category_versions', ['version'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop category_versions table
    op.drop_index(op.f('ix_category_versions_version'), table_name='category_versions')
    op.drop_index(op.f('ix_category_versions_id'), table_name='category_versions')
    op.drop_table('category_versions')
