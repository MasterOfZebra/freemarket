"""
Authentication endpoints - JWT with refresh tokens in HttpOnly cookies
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
import time
from collections import defaultdict

import jwt  # type: ignore
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status, Form, Body
from fastapi.routing import APIRoute
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.database import get_db
from backend.models import User, RefreshToken, AuthEvent
from backend.schemas import (
    UserRegister, UserLogin, UserProfile, LoginResponse, TokenResponse,
    RefreshTokenRequest, ChangePasswordRequest
)
from backend.auth import hash_password, verify_password, create_access_token, create_refresh_token, hash_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, get_current_user_optional
from pydantic import BaseModel

# Rate limiting storage (in-memory for simplicity, use Redis in production)
rate_limit_store = defaultdict(list)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 5  # requests
RATE_LIMIT_WINDOW = 60   # seconds


class RateLimitedRoute(APIRoute):
    """Custom APIRoute with rate limiting for auth endpoints"""

    def get_route_handler(self):
        original_route_handler = super().get_route_handler()

        async def rate_limited_route_handler(request: Request):
            # Rate limiting logic
            client_ip = request.client.host if request.client else "unknown"
            current_time = time.time()

            # Clean old requests
            rate_limit_store[client_ip] = [
                req_time for req_time in rate_limit_store[client_ip]
                if current_time - req_time < RATE_LIMIT_WINDOW
            ]

            # Check rate limit
            if len(rate_limit_store[client_ip]) >= RATE_LIMIT_REQUESTS:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )

            # Add current request
            rate_limit_store[client_ip].append(current_time)

            # Call original handler
            return await original_route_handler(request)

        return rate_limited_route_handler

    # Removed get_route_init_args, as the base class does not implement it and it's unnecessary

# Create rate-limited router for auth endpoints
auth_router = APIRouter(route_class=RateLimitedRoute)

# Security configuration
REFRESH_TOKEN_EXPIRE_DAYS = 30    # Long-lived refresh tokens

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 5  # requests per window
RATE_LIMIT_WINDOW = 300  # 5 minutes in seconds
rate_limit_store = defaultdict(list)  # In production, use Redis

router = APIRouter()


def check_rate_limit(client_ip: str, endpoint: str) -> bool:
    """Check if client is within rate limits"""
    key = f"{client_ip}:{endpoint}"
    now = time.time()

    # Clean old entries
    rate_limit_store[key] = [t for t in rate_limit_store[key] if now - t < RATE_LIMIT_WINDOW]

    # Check limit
    if len(rate_limit_store[key]) >= RATE_LIMIT_REQUESTS:
        return False

    # Add current request
    rate_limit_store[key].append(now)
    return True
















def log_auth_event(
    db: Session,
    user_id: Optional[int],
    event_type: str,
    request: Request,
    success: bool = True,
    details: Optional[dict] = None
):
    """Log authentication event for audit"""
    try:
        auth_event = AuthEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            device_id=request.cookies.get("device_id", "unknown"),
            success=success,
            details=details
        )
        db.add(auth_event)
        db.commit()
    except Exception:
        # Don't fail the main operation if logging fails
        db.rollback()


@auth_router.post("/register", response_model=LoginResponse)
async def register_user(
    *,
    response: Response,
    request: Request,
    user_data: UserRegister = Body(...),
    db: Session = Depends(get_db)
):
    """Register new user and return JWT tokens"""
    try:
        # Check if user already exists
        conditions = []
        if user_data.email:
            conditions.append(User.email == user_data.email)
        if user_data.phone:
            conditions.append(User.phone == user_data.phone)
        if user_data.username:
            conditions.append(User.username == user_data.username)

        if conditions:
            existing_user = db.query(User).filter(or_(*conditions)).first()
        else:
            existing_user = None

        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        # Hash password
        password_hash = hash_password(user_data.password)

        # Create user
        user = User(
            email=user_data.email,
            phone=user_data.phone,
            username=user_data.username,
            password_hash=password_hash,
            full_name=user_data.full_name,
            telegram_contact=user_data.telegram_contact,
            city=user_data.city
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # Create tokens (same as login)
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token()

        # Store refresh token
        token_hash = hash_refresh_token(refresh_token)
        device_id = request.cookies.get("device_id") or secrets.token_hex(16)

        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            device_id=device_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(db_refresh_token)
        db.commit()

        # Set refresh token in HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        # Set device ID cookie
        response.set_cookie(
            key="device_id",
            value=device_id,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=365 * 24 * 60 * 60  # 1 year
        )

        # Log successful registration
        log_auth_event(db, user.id if isinstance(user.id, int) else None, "register", request, True)

        return LoginResponse(
            user=UserProfile.from_orm(user),
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Registration failed: {str(e)}")
        print(f"[ERROR] Traceback: {error_details}")
        log_auth_event(db, None, "register", request, False, {"error": str(e), "traceback": error_details})
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@auth_router.post("/login", response_model=LoginResponse)
async def login_user(
    response: Response,
    request: Request,
    password: str = Form(...),
    email: Optional[str] = Form(None),
    identifier: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Login user and return JWT tokens"""
    try:
        # Use email if provided, otherwise identifier
        login_identifier = email or identifier

        # Find user by identifier
        user = db.query(User).filter(
            or_(
                User.email == login_identifier,
                User.phone == login_identifier,
                User.username == login_identifier
            )
        ).first()

        if not user or not verify_password(password, user.password_hash):  # type: ignore
            log_auth_event(db, int(user.id) if user and isinstance(user.id, int) else None, "failed_login", request, False)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if user.is_active is False:  # type: ignore
            raise HTTPException(status_code=401, detail="Account is disabled")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)  # type: ignore
        db.commit()

        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token()

        # Store refresh token
        token_hash = hash_refresh_token(refresh_token)
        device_id = request.cookies.get("device_id") or secrets.token_hex(16)

        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            device_id=device_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(db_refresh_token)
        db.commit()

        # Set refresh token in HttpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        # Set device ID cookie
        response.set_cookie(
            key="device_id",
            value=device_id,
            secure=True,
            samesite="lax",
            max_age=365 * 24 * 60 * 60  # 1 year
        )

        # Log successful login
        log_auth_event(db, user.id if isinstance(user.id, int) else None, "login", request, True)

        return LoginResponse(
            user=UserProfile.from_orm(user),
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"[ERROR] Login failed: {str(e)}")
        print(f"[ERROR] Traceback: {error_details}")
        log_auth_event(db, None, "login", request, False, {"error": str(e), "traceback": error_details})
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token from cookie"""
    try:
        refresh_token = request.cookies.get("refresh_token")
        device_id = request.cookies.get("device_id")

        if not refresh_token or not device_id:
            raise HTTPException(status_code=401, detail="Refresh token missing")

        # Hash the provided token
        token_hash = hash_refresh_token(refresh_token)

        # Find valid refresh token
        db_token = db.query(RefreshToken).filter(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.device_id == device_id,
                RefreshToken.is_revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        ).first()

        if not db_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Get user
        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user or user.is_active is False:  # type: ignore
            raise HTTPException(status_code=401, detail="User not found or inactive")

        # Create new tokens
        new_access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token()

        # Revoke old refresh token
        db_token.is_revoked = True  # type: ignore
        db_token.revoked_at = datetime.now(timezone.utc)  # type: ignore
        db_token.revoked_reason = "token_rotation"  # type: ignore

        # Store new refresh token
        new_token_hash = hash_refresh_token(new_refresh_token)
        new_db_token = RefreshToken(
            user_id=user.id,
            token_hash=new_token_hash,
            device_id=device_id,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
            expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        )

        db.add(new_db_token)
        db.commit()

        # Set new refresh token in cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        # Log refresh
        log_auth_event(db, user.id if isinstance(user.id, int) else None, "refresh", request, True)

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Token refresh failed")


@auth_router.post("/logout")
async def logout_user(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user by revoking refresh tokens"""
    try:
        device_id = request.cookies.get("device_id")

        if device_id:
            # Revoke all refresh tokens for this user and device
            db.query(RefreshToken).filter(
                and_(
                    RefreshToken.user_id == current_user.id,
                    RefreshToken.device_id == device_id,
                    RefreshToken.is_revoked == False
                )
            ).update({
                "is_revoked": True,
                "revoked_at": datetime.now(timezone.utc),
                "revoked_reason": "logout"
            })
            db.commit()

        # Clear cookies
        response.delete_cookie(key="refresh_token")
        response.delete_cookie(key="device_id")

        # Log logout
        log_auth_event(db, current_user.id if isinstance(current_user.id, int) else None, "logout", request, True)

        return {"message": "Successfully logged out"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Logout failed")


@auth_router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.password_hash):  # type: ignore
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash new password
        current_user.password_hash = hash_password(password_data.new_password)  # type: ignore
        current_user.updated_at = datetime.now(timezone.utc)  # type: ignore

        # Revoke all refresh tokens for security (token rotation)
        db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.now(timezone.utc),
            "revoked_reason": "password_change"
        })

        db.commit()

        return {"message": "Password changed successfully. All other sessions have been logged out for security."}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Password change failed")


@auth_router.post("/revoke-sessions")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke all refresh tokens (logout from all devices)"""
    try:
        revoked_count = db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.now(timezone.utc),
            "revoked_reason": "manual_revoke"
        })

        db.commit()

        # Log the event
        log_auth_event(db, current_user.id if isinstance(current_user.id, int) else None, "revoke_all_sessions", Request(scope={}), True, {"revoked_count": revoked_count})

        return {"message": f"All sessions revoked successfully. {revoked_count} sessions logged out."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to revoke sessions")


@auth_router.get("/me")
async def get_current_user_profile(
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get current user profile (returns null if not authenticated)"""
    if not current_user:
        # Return 200 with null instead of 401 to avoid console errors
        # Frontend will check if user is null to determine auth status
        return {"user": None, "authenticated": False}
    return {"user": UserProfile.from_orm(current_user), "authenticated": True}
