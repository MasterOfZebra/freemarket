"""
Authentication utilities and dependencies
"""

import os
import hashlib
import secrets
import jwt  # type: ignore
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User

# Password hashing with Argon2id (more secure than bcrypt)
try:
    from passlib.hash import argon2
    HAS_ARGON2 = True
    HAS_BCRYPT = False
except ImportError:
    # Fallback to bcrypt if argon2 is not available
    HAS_ARGON2 = False
    try:
        import bcrypt  # type: ignore
        HAS_BCRYPT = True
    except ImportError:
        HAS_BCRYPT = False

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash password with Argon2id or bcrypt as fallback"""
    if HAS_ARGON2:
        return argon2.hash(password)
    elif HAS_BCRYPT:
        # Fallback to bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    else:
        # No password hashing available - this should not happen in production
        raise RuntimeError("No password hashing library available. Install passlib[argon2] or bcrypt.")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    if HAS_ARGON2:
        return argon2.verify(plain_password, hashed_password)
    elif HAS_BCRYPT:
        # Fallback to bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    else:
        # No password hashing available - this should not happen in production
        raise RuntimeError("No password hashing library available. Install passlib[argon2] or bcrypt.")


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    """Create cryptographically secure refresh token"""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Check if user is active (loaded value should be boolean)
    is_active = getattr(user, "is_active", True)
    if not is_active:  # type: ignore
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from JWT token, or None if not authenticated"""
    if not credentials:
        return None

    try:
        payload = verify_token(credentials.credentials)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        if not user or user.is_active is False:  # type: ignore
            return None

        return user
    except HTTPException:
        # Token expired or invalid - return None instead of raising
        return None


__all__ = [
    "hash_password", "verify_password", "verify_token",
    "create_access_token", "create_refresh_token", "hash_refresh_token",
    "get_current_user", "get_current_user_optional",
    "ACCESS_TOKEN_EXPIRE_MINUTES"
]
