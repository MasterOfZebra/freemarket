"""Add RBAC schema with roles, permissions, and enhanced audit log

Revision ID: q5r6s7t8u9v0w
Revises: p4q5r6s7t8u9
Create Date: 2025-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'q5r6s7t8u9v0w'
down_revision: Union[str, tuple, None] = 'p4q5r6s7t8u9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add RBAC tables, enhance audit log, and add role_id to users"""

    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create role_permissions junction table
    op.create_table('role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    # Create complaints table for moderation
    op.create_table('complaints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('complainant_user_id', sa.Integer(), nullable=True),
        sa.Column('reported_user_id', sa.Integer(), nullable=True),
        sa.Column('reported_listing_id', sa.Integer(), nullable=True),
        sa.Column('complaint_type', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), server_default='pending', nullable=True),
        sa.Column('moderator_user_id', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['complainant_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reported_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reported_listing_id'], ['listings.id'], ),
        sa.ForeignKeyConstraint(['moderator_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add role_id to users (nullable initially)
    op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_users_role_id', 'users', 'roles', ['role_id'], ['id'])

    # Enhance admin_audit_log
    op.add_column('admin_audit_log', sa.Column('request_id', sa.String(), nullable=True))
    op.add_column('admin_audit_log', sa.Column('user_agent', sa.Text(), nullable=True))
    op.add_column('admin_audit_log', sa.Column('diff', sa.JSON(), nullable=True))

    # Insert default roles
    op.execute("INSERT INTO roles (name) VALUES ('user'), ('moderator'), ('admin')")

    # Insert default permissions
    permissions = [
        'users.view', 'users.edit', 'users.ban', 'users.delete',
        'listings.view', 'listings.edit', 'listings.moderate', 'listings.delete',
        'complaints.view', 'complaints.resolve',
        'audit.view',
        'admin.impersonate', 'admin.settings'
    ]

    for perm in permissions:
        op.execute(f"INSERT INTO permissions (name) VALUES ('{perm}')")

    # Assign permissions to roles
    # Admin gets all permissions
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'admin'
    """)

    # Moderator gets limited permissions
    moderator_perms = [
        'users.view', 'users.edit', 'users.ban',
        'listings.view', 'listings.edit', 'listings.moderate',
        'complaints.view', 'complaints.resolve'
    ]
    for perm in moderator_perms:
        op.execute(f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'moderator' AND p.name = '{perm}'
        """)

    # User gets minimal permissions
    user_perms = ['listings.view']
    for perm in user_perms:
        op.execute(f"""
            INSERT INTO role_permissions (role_id, permission_id)
            SELECT r.id, p.id
            FROM roles r, permissions p
            WHERE r.name = 'user' AND p.name = '{perm}'
        """)


def downgrade() -> None:
    """Remove RBAC schema and revert changes"""

    # Remove role_permissions
    op.drop_table('role_permissions')

    # Remove permissions
    op.drop_table('permissions')

    # Remove complaints
    op.drop_table('complaints')

    # Remove role_id from users
    op.drop_constraint('fk_users_role_id', 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')

    # Remove audit log enhancements
    op.drop_column('admin_audit_log', 'request_id')
    op.drop_column('admin_audit_log', 'user_agent')
    op.drop_column('admin_audit_log', 'diff')

    # Remove roles
    op.drop_table('roles')
