"""
Data validation utilities
"""
from typing import Optional
import re


def validate_username(username: str) -> bool:
    """Validate username format"""
    if not username or len(username) < 3 or len(username) > 50:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_telegram_id(telegram_id: str) -> bool:
    """Validate Telegram username/ID"""
    if not telegram_id:
        return False
    # Telegram usernames start with @ and contain alphanumeric + underscore
    if telegram_id.startswith('@'):
        telegram_id = telegram_id[1:]
    return bool(re.match(r'^[a-zA-Z0-9_]{5,32}$', telegram_id))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input"""
    if not text:
        return ""
    # Remove leading/trailing whitespace
    text = text.strip()
    # Limit length if specified
    if max_length:
        text = text[:max_length]
    return text
