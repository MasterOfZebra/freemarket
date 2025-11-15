"""Merge telegram_id and auth_events heads

Revision ID: p4q5r6s7t8u9
Revises: n2o3p4q5r6s7, o3p4q5r6s7t8
Create Date: 2025-11-15 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'p4q5r6s7t8u9'
down_revision: Union[str, None] = ('n2o3p4q5r6s7', 'o3p4q5r6s7t8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads - no changes needed, just merge point."""
    pass


def downgrade() -> None:
    """Merge heads - no changes needed, just merge point."""
    pass

