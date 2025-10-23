from datetime import datetime, timedelta, timezone
from typing import Any
import secrets
import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Cấu hình password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Thuật toán JWT
ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Token đã hết hạn
        return None
    except jwt.JWTError:
        # Token không hợp lệ
        return None


def verify_token(token: str, token_type: str = "access") -> str | None:
    payload = decode_token(token)
    if payload is None:
        return None
    
    # Kiểm tra loại token
    if payload.get("type") != token_type:
        return None
    
    # Lấy subject (user_id)
    token_data: str | None = payload.get("sub")
    return token_data


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    # Kiểm tra độ dài tối thiểu
    if len(password) < 8:
        return False, "Mật khẩu phải có ít nhất 8 ký tự"
    
    # Kiểm tra độ dài tối đa
    if len(password) > 40:
        return False, "Mật khẩu không được quá 40 ký tự"
    
    # Kiểm tra có chứa chữ hoa
    if not any(c.isupper() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ hoa"
    
    # Kiểm tra có chứa chữ thường
    if not any(c.islower() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ thường"
    
    # Kiểm tra có chứa số
    if not any(c.isdigit() for c in password):
        return False, "Mật khẩu phải có ít nhất 1 chữ số"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Mật khẩu phải có ít nhất 1 ký tự đặc biệt"

    return True, ""


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    
    encoded_jwt = jwt.encode(
        {
            "exp": exp,
            "nbf": now.timestamp(),
            "sub": email,
            "type": "password_reset"
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        # Kiểm tra loại token
        if decoded_token.get("type") != "password_reset":
            return None
        
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def generate_email_verification_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    
    encoded_jwt = jwt.encode(
        {
            "exp": exp,
            "nbf": now.timestamp(),
            "sub": email,
            "type": "email_verification"
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_email_verification_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        # Kiểm tra loại token
        if decoded_token.get("type") != "email_verification":
            return None
        
        return decoded_token["sub"]
    except jwt.JWTError:
        return None


def generate_random_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_coupon_code(length: int = 8) -> str:
    """
    Tạo mã coupon ngẫu nhiên.
    Chỉ bao gồm chữ in hoa và số để dễ đọc và nhập.
    
    Args:
        length: Độ dài của mã coupon
        
    Returns:
        str: Mã coupon ngẫu nhiên
    """
    # Chỉ sử dụng chữ in hoa và số, loại bỏ các ký tự dễ nhầm lẫn (0, O, I, 1)
    characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_order_number() -> str:
    """
    Tạo mã đơn hàng unique.
    Format: PREFIX + TIMESTAMP + RANDOM
    Ví dụ: FE20251022174059ABC123
    
    Returns:
        str: Mã đơn hàng unique
    """
    # Lấy timestamp hiện tại
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Tạo phần random 6 ký tự
    random_part = ''.join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    
    # Kết hợp: PREFIX + TIMESTAMP + RANDOM
    order_number = f"{settings.ORDER_NUMBER_PREFIX}{timestamp}{random_part}"
    
    return order_number


def generate_transaction_code() -> str:
    """
    Tạo mã giao dịch thanh toán unique.
    Format: TXN + TIMESTAMP + RANDOM
    Ví dụ: TXN20251022174059XYZ789
    
    Returns:
        str: Mã giao dịch unique
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = ''.join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    
    return f"TXN{timestamp}{random_part}"


def generate_sku(
    category_code: str = "GEN",
    color_code: str = "00",
    size_code: str = "00"
) -> str:
    """
    Tạo SKU (Stock Keeping Unit) cho biến thể sản phẩm.
    Format: CATEGORY-COLOR-SIZE-RANDOM
    Ví dụ: SHOE-RED-42-ABC123
    
    Args:
        category_code: Mã danh mục sản phẩm
        color_code: Mã màu sắc
        size_code: Mã kích cỡ
        
    Returns:
        str: SKU unique
    """
    # Tạo phần random 6 ký tự
    random_part = ''.join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
    
    # Chuẩn hóa các mã thành chữ in hoa
    category_code = category_code.upper()
    color_code = color_code.upper()
    size_code = str(size_code).upper()
    
    return f"{category_code}-{color_code}-{size_code}-{random_part}"


def hash_api_key(api_key: str) -> str:
    return pwd_context.hash(api_key)


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    return pwd_context.verify(plain_api_key, hashed_api_key)
