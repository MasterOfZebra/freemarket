"""Change telegram_id from Integer to BigInteger

Revision ID: o3p4q5r6s7t8
Revises: m1n2o3p4q5r6
Create Date: 2025-11-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'o3p4q5r6s7t8'
down_revision: Union[str, None] = 'm1n2o3p4q5r6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change telegram_id column from Integer to BigInteger."""
    # PostgreSQL: ALTER COLUMN to change type
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=True)


def downgrade() -> None:
    """Change telegram_id column back from BigInteger to Integer."""
    # Note: This may fail if there are values > 2^31-1
    op.alter_column('users', 'telegram_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    existing_nullable=True)

