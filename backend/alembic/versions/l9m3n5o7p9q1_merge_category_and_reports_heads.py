"""merge category constraint fix and reports table heads

Revision ID: l9m3n5o7p9q1
Revises: 668bc94471e9, k9l2m8n4o6p
Create Date: 2025-11-10 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'l9m3n5o7p9q1'
down_revision: Union[str, Sequence[str], None] = ('668bc94471e9', 'k9l2m8n4o6p')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads: category constraint fix + reports table."""
    pass


def downgrade() -> None:
    """Unmerge heads: category constraint fix + reports table."""
    pass
