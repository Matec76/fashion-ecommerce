"""
Core package initialization.

Export core utilities.
"""

from app.core.config import settings
from app.core.db import engine, async_session_maker, init_db, get_db
from app.core.security import (
    # Password
    get_password_hash,
    verify_password,
    validate_password_strength,
    # Tokens
    create_access_token,
    create_refresh_token,
    decode_token,
    # Password Reset
    generate_password_reset_token,
    # Email Verification
    generate_email_verification_token,
    # Generators
    generate_random_token,
    generate_coupon_code,
    generate_order_number,
    generate_transaction_code,
    generate_sku,
    # API Key
    hash_api_key,
    verify_api_key,
)

__all__ = [
    # Config
    "settings",
    # Database
    "engine",
    "async_session_maker",
    "init_db",
    "get_db",
    # Security - Password
    "get_password_hash",
    "verify_password",
    "validate_password_strength",
    # Security - Tokens
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_password_reset_token",
    "generate_email_verification_token",
    # Security - Generators
    "generate_random_token",
    "generate_coupon_code",
    "generate_order_number",
    "generate_transaction_code",
    "generate_sku",
    # Security - API Key
    "hash_api_key",
    "verify_api_key",
]