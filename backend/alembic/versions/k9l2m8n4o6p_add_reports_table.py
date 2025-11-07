"""add reports table for moderation system

Revision ID: k9l2m8n4o6p
Revises: j8k9l0m1n2o3
Create Date: 2025-11-08 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k9l2m8n4o6p'
down_revision: Union[str, Sequence[str], None] = 'j8k9l0m1n2o3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add reports table for user moderation system."""

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reporter_id', sa.Integer(), nullable=False),
        sa.Column('target_listing_id', sa.Integer(), nullable=True),
        sa.Column('target_user_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_listing_id'], ['listing_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indexes
    op.create_index('ix_reports_reporter_id', 'reports', ['reporter_id'], unique=False)
    op.create_index('ix_reports_target_listing_id', 'reports', ['target_listing_id'], unique=False)
    op.create_index('ix_reports_target_user_id', 'reports', ['target_user_id'], unique=False)
    op.create_index('ix_reports_reason', 'reports', ['reason'], unique=False)
    op.create_index('ix_reports_status', 'reports', ['status'], unique=False)
    op.create_index('ix_reports_created_at', 'reports', ['created_at'], unique=False)
    op.create_index('ix_reports_admin_id', 'reports', ['admin_id'], unique=False)


def downgrade() -> None:
    """Remove reports table."""

    # Drop indexes
    op.drop_index('ix_reports_admin_id', table_name='reports')
    op.drop_index('ix_reports_created_at', table_name='reports')
    op.drop_index('ix_reports_status', table_name='reports')
    op.drop_index('ix_reports_reason', table_name='reports')
    op.drop_index('ix_reports_target_user_id', table_name='reports')
    op.drop_index('ix_reports_target_listing_id', table_name='reports')
    op.drop_index('ix_reports_reporter_id', table_name='reports')

    # Drop table
    op.drop_table('reports')
