"""merge multiple heads

Revision ID: cbfc66708806
Revises: 001_add_exchange_types, 50c3593832b4
Create Date: 2025-11-03 19:53:21.455365

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbfc66708806'
down_revision: Union[str, Sequence[str], None] = ('ecee305c0829', '001_add_exchange_types', '50c3593832b4', 'cf5a32f4e1d5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
