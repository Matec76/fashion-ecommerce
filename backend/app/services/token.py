import logging
import jwt
from typing import Tuple, Optional
from datetime import datetime, timedelta, timezone

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.core.security import (
    create_refresh_token, 
    generate_email_verification_token, 
    generate_password_reset_token
)

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(
        self, 
        identifier: str, 
        action: str, 
        max_attempts: int, 
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Kiểm tra giới hạn request.
        Nếu Redis chết, trả về True (Fail-open) để không chặn người dùng.
        """
        key = f"rate_limit:{action}:{identifier}"
        try:
            current_attempts = await self.redis.incr(key)
            if current_attempts == 1:
                await self.redis.expire(key, window_seconds)
                
            if current_attempts > max_attempts:
                return False, 0
            return True, max_attempts - current_attempts
        except Exception as e:
            logger.error(f"Redis Rate Limit Error: {e}")
            return True, max_attempts

    async def reset_rate_limit(self, identifier: str, action: str) -> None:
        key = f"rate_limit:{action}:{identifier}"
        try:
            await self.redis.delete(key)
        except Exception:
            pass

    
    async def create_refresh_token(self, user_id: int) -> str:
        """Tạo Refresh Token (JWT có jti)"""
        return create_refresh_token(subject=user_id)

    async def create_email_verification_token(self, email: str) -> str:
        """Tạo Email Token (JWT có jti)"""
        return generate_email_verification_token(email=email)

    async def create_password_reset_token(self, email: str) -> str:
        """Tạo Password Reset Token (JWT có jti)"""
        return generate_password_reset_token(email=email)
    

    async def verify_token(self, token: str, required_type: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            token_type = payload.get("type")
            sub = payload.get("sub")
            jti = payload.get("jti")
            iat = payload.get("iat")

            if token_type != required_type or not sub or not jti:
                return None

            is_blacklisted = await self.redis.get(f"blacklist:{jti}")
            if is_blacklisted:
                logger.warning(f"Blocked attempt with blacklisted token: {jti}")
                return None

            user_id_str = str(sub)
            if user_id_str.isdigit():
                min_iat_key = f"blacklist:user:{user_id_str}:min_iat"
                min_iat = await self.redis.get(min_iat_key)
                
                if min_iat and iat < int(min_iat):
                    logger.warning(f"Blocked old token for user {sub} (issued at {iat} < min {min_iat})")
                    return None

            return user_id_str

        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError as e:
            logger.error(f"JWT Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Redis/System Error verify token: {e}")
            return None
    


    async def revoke_token(self, token: str):
        """
        Thu hồi token (Dùng cho Logout hoặc đánh dấu Email/Pass token đã sử dụng).
        Lấy 'jti' và thời gian hết hạn 'exp', lưu vào Redis.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            now = datetime.now(timezone(timedelta(hours=7))).timestamp()
            ttl = int(exp - now)
            
            if ttl > 0:
                await self.redis.setex(f"blacklist:{jti}", ttl, "revoked")
                logger.info(f"Revoked/Blacklisted token: {jti}")
                
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
    

    async def revoke_all_user_tokens(self, user_id: int):
        """
        Đặt mốc thời gian: Tất cả token phát hành TRƯỚC giờ này đều vô hiệu.
        Key này sẽ sống bằng thời gian của Refresh Token.
        """
        now_ts = int(datetime.now(timezone(timedelta(hours=7))).timestamp())
        key = f"blacklist:user:{user_id}:min_iat"
        
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        
        await self.redis.setex(key, ttl, now_ts)
        logger.info(f"Revoked ALL tokens for user {user_id} issued before {now_ts}")

    
    async def verify_refresh_token(self, token: str) -> Optional[int]:
        sub = await self.verify_token(token, "refresh")
        return int(sub) if sub else None

    async def verify_email_token(self, token: str) -> Optional[str]:
        return await self.verify_token(token, "email_verification")

    async def verify_password_reset_token(self, token: str) -> Optional[str]:
        return await self.verify_token(token, "password_reset")

async def get_token_service_dep(request: Request) -> TokenService:
    redis = getattr(request.app.state, "redis", None)
    return TokenService(redis)