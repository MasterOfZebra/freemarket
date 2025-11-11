"""add missing telegram fields and rating fields to users table

Revision ID: m1n2o3p4q5r6
Revises: l9m3n5o7p9q1
Create Date: 2025-11-11 18:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm1n2o3p4q5r6'
down_revision: Union[str, None] = 'l9m3n5o7p9q1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing telegram and rating fields to users table."""
    # Add rating fields
    op.add_column('users', sa.Column('rating_count', sa.Integer(), server_default='0', nullable=True))
    op.add_column('users', sa.Column('last_rating_update', sa.DateTime(timezone=True), nullable=True))
    
    # Add telegram fields
    op.add_column('users', sa.Column('telegram_username', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('telegram_first_name', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove telegram and rating fields from users table."""
    op.drop_column('users', 'telegram_first_name')
    op.drop_column('users', 'telegram_username')
    op.drop_column('users', 'last_rating_update')
    op.drop_column('users', 'rating_count')

