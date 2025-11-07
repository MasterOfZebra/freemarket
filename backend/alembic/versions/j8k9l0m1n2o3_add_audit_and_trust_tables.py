"""add audit and trust tables

Revision ID: j8k9l0m1n2o3
Revises: i5f8g9h2j7k4
Create Date: 2025-11-08 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j8k9l0m1n2o3'
down_revision: Union[str, Sequence[str], None] = 'i5f8g9h2j7k4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user action log and trust index tables."""

    # Create user_action_log table
    op.create_table(
        'user_action_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_trust_index table
    op.create_table(
        'user_trust_index',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('trust_score', sa.Float(), nullable=False),
        sa.Column('weighted_rating', sa.Float(), nullable=False),
        sa.Column('exchanges_completed', sa.Integer(), nullable=False),
        sa.Column('reviews_received', sa.Integer(), nullable=False),
        sa.Column('reports_filed', sa.Integer(), nullable=False),
        sa.Column('reports_received', sa.Integer(), nullable=False),
        sa.Column('account_age_days', sa.Integer(), nullable=False),
        sa.Column('last_activity_days', sa.Integer(), nullable=False),
        sa.Column('last_calculated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_trust_index_user_id')
    )

    # Indexes
    op.create_index('ix_user_action_log_user_id', 'user_action_log', ['user_id'], unique=False)
    op.create_index('ix_user_action_log_action_type', 'user_action_log', ['action_type'], unique=False)
    op.create_index('ix_user_action_log_created_at', 'user_action_log', ['created_at'], unique=False)
    op.create_index('ix_user_trust_index_user_id', 'user_trust_index', ['user_id'], unique=False)
    op.create_index('ix_user_trust_index_trust_score', 'user_trust_index', ['trust_score'], unique=False)
    op.create_index('ix_user_trust_index_last_calculated', 'user_trust_index', ['last_calculated'], unique=False)


def downgrade() -> None:
    """Remove audit and trust tables."""

    # Drop indexes
    op.drop_index('ix_user_trust_index_last_calculated', table_name='user_trust_index')
    op.drop_index('ix_user_trust_index_trust_score', table_name='user_trust_index')
    op.drop_index('ix_user_trust_index_user_id', table_name='user_trust_index')
    op.drop_index('ix_user_action_log_created_at', table_name='user_action_log')
    op.drop_index('ix_user_action_log_action_type', table_name='user_action_log')
    op.drop_index('ix_user_action_log_user_id', table_name='user_action_log')

    # Drop tables
    op.drop_table('user_trust_index')
    op.drop_table('user_action_log')
