"""
Admin panel setup with FastAPI-Admin and RBAC integration.

Provides secure admin interface for managing users, listings, and complaints.
"""

import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi_admin.app import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider
from fastapi_admin.resources import ModelView, Field
from fastapi_admin.widgets import displays, inputs
from fastapi_admin.enums import Method
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship, Session
from pydantic import BaseModel

from backend.database import get_db
from backend.models import User, Listing, ListingItem
from backend.auth import get_current_user
from backend.admin_config import ADMIN_CONFIG, ADMIN_SECURITY


class AdminUser(BaseModel):
    """Pydantic model for admin user authentication"""
    username: str
    password: str


class CustomLoginProvider(UsernamePasswordProvider):
    """Custom login provider with RBAC check"""

    async def login(self, username: str, password: str):
        """Override login to check admin role"""
        from backend.auth import verify_password

        # Get user from database
        db = next(get_db())
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return None

            # Check password
            if not verify_password(password, user.password_hash):
                return None

            # Check if user has admin or moderator role
            if not user.role_id:
                return None

            # Get role name
            role_query = db.execute("SELECT name FROM roles WHERE id = %s", (user.role_id,))
            role_result = role_query.fetchone()

            if not role_result or role_result[0] not in ['admin', 'moderator']:
                return None

            # Create admin user object
            from fastapi_admin.models import AdminUser
            admin_user = AdminUser(
                id=user.id,
                username=user.username,
                email=user.email,
                role=role_result[0]
            )

            return admin_user

        finally:
            db.close()


# User Admin View
class UserAdmin(ModelView):
    model = User
    icon = "fas fa-users"
    page_size = 50

    fields = [
        Field(name="id", label="ID", display=displays.Display()),
        Field(name="username", label="Username", input=inputs.TextInput()),
        Field(name="email", label="Email", input=inputs.EmailInput()),
        Field(name="full_name", label="Full Name", input=inputs.TextInput()),
        Field(name="phone", label="Phone", input=inputs.TextInput()),
        Field(name="role_id", label="Role ID", input=inputs.NumberInput()),
        Field(name="is_active", label="Active", input=inputs.SwitchInput()),
        Field(name="is_deleted", label="Deleted", input=inputs.SwitchInput()),
        Field(name="created_at", label="Created", display=displays.DatetimeDisplay()),
    ]

    async def get_queryset(self, request, queryset):
        """Filter users based on admin role"""
        # Get current admin user from session/context
        admin_user = getattr(request.state, 'user', None)
        if admin_user and admin_user.role == 'moderator':
            # Moderators can only see non-admin users
            # Get admin role ID dynamically
            db = next(get_db())
            try:
                admin_role = db.execute("SELECT id FROM roles WHERE name = 'admin'").fetchone()
                if admin_role:
                    return queryset.filter(User.role_id != admin_role[0])
            finally:
                db.close()
        return queryset

    async def has_permission(self, request, action: str) -> bool:
        """Check permissions for actions"""
        admin_user = getattr(request.state, 'user', None)
        if not admin_user:
            return False

        # Admins can do everything
        if admin_user.role == 'admin':
            return True

        # Moderators can only view and edit users (not delete)
        if admin_user.role == 'moderator':
            return action in ['list', 'detail', 'edit']

        return False


# Listing Admin View
class ListingAdmin(ModelView):
    model = Listing
    icon = "fas fa-list"
    page_size = 50

    fields = [
        Field(name="id", label="ID", display=displays.Display()),
        Field(name="user_id", label="User ID", input=inputs.NumberInput()),
        Field(name="title", label="Title", input=inputs.TextInput()),
        Field(name="description", label="Description", input=inputs.TextArea()),
        Field(name="moderation_status", label="Status", input=inputs.SelectInput(
            choices=[('pending', 'Pending'), ('approved', 'Approved'),
                    ('rejected', 'Rejected'), ('archived', 'Archived')]
        )),
        Field(name="is_deleted", label="Deleted", input=inputs.SwitchInput()),
        Field(name="created_at", label="Created", display=displays.DatetimeDisplay()),
    ]


# Complaints Admin View (placeholder - table will be created later)
class ComplaintAdmin(ModelView):
    # This will be implemented after complaints table is created
    pass


def setup_admin_panel(app: FastAPI):
    """Setup FastAPI-Admin panel with RBAC"""

    # Configure admin app
    admin_app.configure(
        title=ADMIN_CONFIG["title"],
        logo_url=ADMIN_CONFIG["logo_url"],
        login_provider=CustomLoginProvider(
            login_logo_url=ADMIN_CONFIG["login_logo_url"],
            admin_path=ADMIN_CONFIG["admin_path"],
        ),
        database_url=ADMIN_CONFIG["database_url"],
        redis_url=ADMIN_CONFIG["redis_url"],
        language=ADMIN_CONFIG["language"],
        theme=ADMIN_CONFIG["theme"],
    )

    # Register views
    admin_app.register_model_view(UserAdmin)
    admin_app.register_model_view(ListingAdmin)

    # Mount admin app
    app.mount(ADMIN_CONFIG["admin_path"], admin_app, name="admin")

    # Add middleware to set admin user context for admin routes
    @app.middleware("http")
    async def admin_user_context(request, call_next):
        """Set admin user context for admin routes"""
        if request.url.path.startswith(ADMIN_CONFIG["admin_path"]):
            # Try to get user from session (this is simplified)
            # In production, you'd get user from admin session
            pass
        return await call_next(request)

    print(f"🔧 Admin panel configured at {ADMIN_CONFIG['admin_path']}")


def check_admin_access(user: User = Depends(get_current_user)) -> User:
    """Dependency to check if user has admin/moderator access"""
    if not user.role_id:
        raise HTTPException(status_code=403, detail="Admin access required")

    # This would need to be enhanced with actual role checking
    # For now, assume role_id 1=admin, 2=moderator, 3=user
    if user.role_id not in [1, 2]:  # admin, moderator
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return user


# Additional admin API endpoints
def setup_admin_api(app: FastAPI):
    """Setup additional admin API endpoints"""

    @app.post("/admin/generate-token")
    async def generate_user_token(
        user_id: int,
        scope: Optional[str] = "read",
        ttl_hours: Optional[int] = 24,
        admin: User = Depends(check_admin_access),
        db: Session = Depends(get_db)
    ):
        """Generate scoped JWT token for a user (admin only)"""
        from backend.auth import create_access_token
        from datetime import timedelta
        import uuid

        # Check if target user exists
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Create scoped token
        token_data = {
            "sub": str(user_id),
            "scope": scope,
            "generated_by": admin.id,
            "token_id": str(uuid.uuid4())
        }

        token = create_access_token(
            token_data,
            expires_delta=timedelta(hours=ttl_hours)
        )

        # Log token generation
        audit_entry = {
            "admin_user_id": admin.id,
            "action": "generate_token",
            "target_type": "user",
            "target_id": user_id,
            "details": {
                "scope": scope,
                "ttl_hours": ttl_hours,
                "token_id": token_data["token_id"]
            }
        }

        # Insert audit log (will be implemented)
        # await log_admin_action(db, audit_entry)

        return {
            "token": token,
            "user_id": user_id,
            "scope": scope,
            "expires_in_hours": ttl_hours,
            "generated_by": admin.username
        }


__all__ = [
    "setup_admin_panel",
    "setup_admin_api",
    "check_admin_access"
]
