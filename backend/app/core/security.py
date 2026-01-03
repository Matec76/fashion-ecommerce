from datetime import datetime, timedelta, timezone
from typing import Any
import secrets
import jwt
import uuid
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
        subject: str | Any, 
        expires_delta: timedelta | None = None,
        role_id: int = None
    ) -> str:
    if expires_delta:
        expire = datetime.now(timezone(timedelta(hours=7))) + expires_delta
    else:
        expire = datetime.now(timezone(timedelta(hours=7))) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }

    if role_id is not None:
        to_encode["role_id"] = role_id
        
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone(timedelta(hours=7))) + expires_delta
    else:
        expire = datetime.now(timezone(timedelta(hours=7))) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    token_id = str(uuid.uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": token_id
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None



def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự"
    
    if len(password) > 40:
        return False, "Mật khẩu không được quá 40 ký tự"
    
    if not any(c.isupper() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ hoa"
    
    if not any(c.islower() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ thường"
    
    if not any(c.isdigit() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ số"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Mật khẩu phải có ít nhất 1 ký tự đặc biệt"

    return True, ""


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone(timedelta(hours=7)))
    expires = now + delta
    
    token_id = str(uuid.uuid4())
    encoded_jwt = jwt.encode(
        {
            "exp": expires,
            "nbf": now,
            "sub": email,
            "type": "password_reset",
            "jti": token_id
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def generate_email_verification_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone(timedelta(hours=7)))
    expires = now + delta
    
    token_id = str(uuid.uuid4())
    encoded_jwt = jwt.encode(
        {
            "exp": expires,
            "nbf": now,
            "sub": email,
            "type": "email_verification",
            "jti": token_id
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def generate_random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_coupon_code(length: int = 8) -> str:
    """Generate coupon code using config length default."""
    characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_order_number() -> str:
    """
    Generate random order number (Utility fallback).
    Note: Main logic is usually in CRUDOrder using DB sequence.
    """
    timestamp = datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d%H%M%S")
    
    random_part = ''.join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    
    order_number = f"{settings.ORDER_NUMBER_PREFIX}{timestamp}{random_part}"
    
    return order_number


def generate_transaction_code() -> str:
    timestamp = datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d%H%M%S")
    random_part = ''.join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    
    return f"TXN{timestamp}{random_part}"


def generate_sku(
    category_code: str = "GEN",
    color_code: str = "00",
    size_code: str = "00"
) -> str:
    random_part = ''.join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    
    category_code = category_code.upper()
    color_code = color_code.upper()
    size_code = str(size_code).upper()
    
    return f"{category_code}-{color_code}-{size_code}-{random_part}"


def hash_api_key(api_key: str) -> str:
    return pwd_context.hash(api_key)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    return pwd_context.verify(plain_api_key, hashed_api_key)