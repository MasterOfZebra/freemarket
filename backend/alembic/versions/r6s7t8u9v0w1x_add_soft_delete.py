"""Add soft-delete fields for safer admin operations

Revision ID: r6s7t8u9v0w1x
Revises: q5r6s7t8u9v0w
Create Date: 2025-11-16 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r6s7t8u9v0w1x'
down_revision: Union[str, tuple, None] = 'q5r6s7t8u9v0w'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add soft-delete fields and moderation status"""

    # Add soft-delete to users
    op.add_column('users', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_deleted_by', 'users', 'users', ['deleted_by'], ['id'])

    # Add soft-delete to listings
    op.add_column('listings', sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('listings', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('listings', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_listings_deleted_by', 'listings', 'users', ['deleted_by'], ['id'])

    # Add moderation status to listings
    op.add_column('listings', sa.Column('moderation_status', sa.String(20), server_default='pending', nullable=False))
    op.create_check_constraint('ck_listings_moderation_status',
                              'listings',
                              "moderation_status IN ('pending', 'approved', 'rejected', 'archived')")

    # Add indexes for performance
    op.create_index('idx_users_is_deleted', 'users', ['is_deleted'])
    op.create_index('idx_listings_is_deleted', 'listings', ['is_deleted'])
    op.create_index('idx_listings_moderation_status', 'listings', ['moderation_status'])

    # Update existing records to have default values
    op.execute("UPDATE users SET is_deleted = false WHERE is_deleted IS NULL")
    op.execute("UPDATE listings SET is_deleted = false, moderation_status = 'approved' WHERE is_deleted IS NULL")


def downgrade() -> None:
    """Remove soft-delete fields and moderation status"""

    # Remove indexes
    op.drop_index('idx_listings_moderation_status')
    op.drop_index('idx_listings_is_deleted')
    op.drop_index('idx_users_is_deleted')

    # Remove constraints
    op.drop_constraint('ck_listings_moderation_status', 'listings', type_='check')

    # Remove foreign keys
    op.drop_constraint('fk_listings_deleted_by', 'listings', type_='foreignkey')
    op.drop_constraint('fk_users_deleted_by', 'users', type_='foreignkey')

    # Remove columns from listings
    op.drop_column('listings', 'moderation_status')
    op.drop_column('listings', 'deleted_by')
    op.drop_column('listings', 'deleted_at')
    op.drop_column('listings', 'is_deleted')

    # Remove columns from users
    op.drop_column('users', 'deleted_by')
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'is_deleted')
