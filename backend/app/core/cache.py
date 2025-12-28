import logging
from typing import Optional
from fastapi_cache.backends.redis import RedisBackend

logger = logging.getLogger(__name__)

class SafeRedisBackend(RedisBackend):
    """
    Kiểm ta tra lỗi khi tương tác với Redis và xử lý ngoại lệ một cách an toàn.
    Nếu có lỗi xảy ra, ghi log lỗi và tiếp tục hoạt động mà không làm gián đoạn ứng dụng.
    """
    async def get(self, key: str) -> Optional[str]:
        try:
            return await super().get(key)
        except Exception as e:
            logger.error(f"Redis Cache GET Error: {e} -> Fallback to DB")
            return None

    async def set(self, key: str, value: str, expire: Optional[int] = None) -> None:
        try:
            await super().set(key, value, expire)
        except Exception as e:
            logger.error(f"Redis Cache SET Error: {e} -> Skipping cache save")

    async def clear(self, namespace: Optional[str] = None, key: Optional[str] = None) -> int:
        try:
            return await super().clear(namespace, key)
        except Exception as e:
            logger.error(f"Redis Cache CLEAR Error: {e}")
            return 0
            
    async def delete(self, key: str) -> None:
        try:
            await super().delete(key)
        except Exception as e:
            logger.error(f"Redis Cache DELETE Error: {e}")