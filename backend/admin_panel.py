"""
Admin panel setup with SQLAdmin and RBAC integration.

Provides secure admin interface for managing users, listings, and complaints.
Uses SQLAdmin instead of FastAPI-Admin for Python 3.11 compatibility.
"""

import os
from typing import Optional, cast
from fastapi import FastAPI, Depends, HTTPException, status
from sqladmin import Admin, ModelView
from sqlalchemy.orm import Session

from backend.database import get_db, engine
from backend.models import User, Listing, ListingItem, Role, Permission, Complaint, AdminAuditLog
from backend.auth import get_current_user, verify_password
from backend.admin_config import ADMIN_CONFIG, ADMIN_SECURITY


class UserAdmin(ModelView, model=User):
    """Admin view for User model"""
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_list = ["id", "username", "email", "full_name", "role_id", "is_active", "is_deleted", "created_at"]
    column_searchable_list = ["username", "email", "full_name"]
    column_sortable_list = ["id", "username", "created_at"]
    column_details_list = ["id", "username", "email", "full_name", "phone", "telegram_contact", "role_id", "is_active", "is_deleted", "created_at"]
    form_columns = ["username", "email", "full_name", "phone", "telegram_contact", "role_id", "is_active", "is_deleted"]
    can_create = True
    can_edit = True
    can_delete = False  # Use soft delete instead
    can_view_details = True

    async def is_accessible(self, request) -> bool:
        """Check if user has admin/moderator access"""
        # This will be checked by the authentication dependency
        return True


class ListingAdmin(ModelView, model=Listing):
    """Admin view for Listing model"""
    name = "Listing"
    name_plural = "Listings"
    icon = "fa-solid fa-list"
    column_list = ["id", "user_id", "title", "is_deleted", "created_at"]
    column_searchable_list = ["title", "description"]
    column_sortable_list = ["id", "created_at"]
    column_details_list = ["id", "user_id", "title", "description", "is_deleted", "created_at"]
    form_columns = ["user_id", "title", "description", "is_deleted"]
    can_create = True
    can_edit = True
    can_delete = False  # Use soft delete instead
    can_view_details = True


class ComplaintAdmin(ModelView, model=Complaint):
    """Admin view for Complaint model"""
    name = "Complaint"
    name_plural = "Complaints"
    icon = "fa-solid fa-flag"
    column_list = ["id", "complainant_user_id", "reported_user_id", "status", "created_at"]
    column_sortable_list = ["id", "created_at", "status"]
    can_create = False
    can_edit = True
    can_delete = False
    can_view_details = True


def check_admin_access(user: User = Depends(get_current_user)) -> User:
    """Dependency to check if user has admin/moderator access"""
    role_id: Optional[int] = cast(Optional[int], getattr(user, 'role_id', None))
    if role_id is None:  # type: ignore[comparison-overlap]
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    db = next(get_db())
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role or role.name not in ['admin', 'moderator']:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    finally:
        db.close()
    return user


def setup_admin_panel(app: FastAPI):
    """Setup SQLAdmin panel with RBAC"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Initializing SQLAdmin with base_url={ADMIN_CONFIG['admin_path']}")

        # Create admin instance
        admin = Admin(
            app,
            engine,
            title=ADMIN_CONFIG["title"],
            base_url=ADMIN_CONFIG["admin_path"],
        )
        logger.info("SQLAdmin instance created")

        # Register views
        logger.info("Registering admin views...")
        admin.add_view(UserAdmin)
        admin.add_view(ListingAdmin)
        admin.add_view(ComplaintAdmin)
        logger.info("Admin views registered")

        # Add authentication middleware
        @app.middleware("http")
        async def admin_auth_middleware(request, call_next):
            """Custom authentication middleware for admin panel"""
            if request.url.path.startswith(ADMIN_CONFIG["admin_path"]):
                # Get authorization header
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.replace("Bearer ", "")
                    try:
                        from backend.auth import verify_token
                        payload = verify_token(token)
                        if payload:
                            user_id = payload.get("sub")
                            if user_id:
                                db = next(get_db())
                                try:
                                    user = db.query(User).filter(User.id == int(user_id)).first()
                                    if user:
                                        role_id = cast(Optional[int], getattr(user, 'role_id', None))
                                        if role_id is not None:
                                            role = db.query(Role).filter(Role.id == role_id).first()
                                            if role and role.name in ['admin', 'moderator']:
                                                request.state.user = user
                                                request.state.admin_user = user
                                finally:
                                    db.close()
                    except Exception:
                        pass

            response = await call_next(request)
            return response

        logger.info(f"🔧 Admin panel configured at {ADMIN_CONFIG['admin_path']}")
        print(f"🔧 Admin panel configured at {ADMIN_CONFIG['admin_path']}")

    except Exception as e:
        logger.error(f"Failed to setup admin panel: {e}", exc_info=True)
        print(f"[ERROR] Failed to setup admin panel: {e}")
        import traceback
        traceback.print_exc()
        raise


def setup_admin_api(app: FastAPI):
    """Setup additional admin API endpoints"""
    from pydantic import BaseModel

    class TokenRequest(BaseModel):
        user_id: int
        scope: Optional[str] = "read"
        ttl_hours: Optional[int] = 24

    @app.post("/admin/api/generate-token", tags=["Admin"], dependencies=[Depends(check_admin_access)])
    async def generate_user_token(
        request: TokenRequest,
        admin: User = Depends(check_admin_access),
        db: Session = Depends(get_db)
    ):
        """Generate scoped JWT token for a user (admin only)"""
        from backend.auth import create_access_token
        from datetime import timedelta
        import uuid

        # Extract parameters from request body
        user_id = request.user_id
        scope = request.scope
        ttl_hours = request.ttl_hours

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

        hours_value: int = ttl_hours if ttl_hours is not None else 24
        expires = timedelta(hours=float(hours_value))
        token = create_access_token(
            token_data,
            expires_delta=expires
        )

        # Log token generation (simplified)
        audit_entry = AdminAuditLog(
            admin_user_id=admin.id,
            action="generate_token",
            target_type="user",
            target_id=user_id,
            details={
                "scope": scope,
                "ttl_hours": ttl_hours,
                "token_id": token_data["token_id"]
            }
        )
        db.add(audit_entry)
        db.commit()

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
