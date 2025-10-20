import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Fashion E-Commerce"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Backend API for Fashion E-Commerce"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    PASSWORD_MIN_LENGTH: int = 8
    
    # Environment
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    # Frontend
    FRONTEND_HOST: str = "http://localhost:5173"
    
    # CORS
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    # Database pool settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False
    
    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    
    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)
    
    EMAIL_TEST_USER: EmailStr = "test@stylex.com"
    EMAIL_TEMPLATES_DIR: str = "app/email-templates"
    
    # Admin User
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_FIRSTNAME: str = "Admin"
    FIRST_SUPERUSER_LASTNAME: str = "System"
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Celery
    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.REDIS_URL
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_EXTENSIONS: list[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "ap-southeast-1"
    S3_BUCKET_NAME: str | None = None
    USE_S3: bool = False
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def s3_enabled(self) -> bool:
        return bool(
            self.USE_S3
            and self.AWS_ACCESS_KEY_ID
            and self.AWS_SECRET_ACCESS_KEY
            and self.S3_BUCKET_NAME
        )
    
    # Payment Gateway - VNPay
    VNPAY_TMN_CODE: str | None = None
    VNPAY_HASH_SECRET: str | None = None
    VNPAY_URL: str = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    VNPAY_RETURN_URL: str = ""
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def vnpay_enabled(self) -> bool:
        return bool(self.VNPAY_TMN_CODE and self.VNPAY_HASH_SECRET)
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Session
    SESSION_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str | None = "logs/app.log"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"

    # Elasticsearch
    ELASTICSEARCH_ENABLED: bool = False
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_INDEX_PREFIX: str = "ecommerce"
    
    # Sentry (Error Tracking)
    SENTRY_DSN: HttpUrl | None = None
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def sentry_enabled(self) -> bool:
        return bool(self.SENTRY_DSN)
    
    # E-commerce Specific Settings
    CURRENCY: str = "VND"
    TAX_RATE: float = 0.0  # 10% VAT
    SHIPPING_FEE_DEFAULT: float = 30000  # 30,000 VND
    FREE_SHIPPING_THRESHOLD: float = 1000000  # Free shipping for orders > 1M VND
    
    # Loyalty Program
    LOYALTY_POINTS_PER_VND: float = 0.001  # 1 point per 1000 VND
    LOYALTY_POINTS_TO_VND: float = 1000  # 1 point = 1000 VND
    
    # Inventory
    LOW_STOCK_THRESHOLD: int = 5
    AUTO_CANCEL_ORDER_HOURS: int = 24  # Auto cancel unpaid orders after 24h
    
    # Order Status
    ORDER_STATUS_PENDING: str = "pending"
    ORDER_STATUS_CONFIRMED: str = "confirmed"
    ORDER_STATUS_PROCESSING: str = "processing"
    ORDER_STATUS_SHIPPED: str = "shipped"
    ORDER_STATUS_DELIVERED: str = "delivered"
    ORDER_STATUS_CANCELLED: str = "cancelled"
    ORDER_STATUS_REFUNDED: str = "refunded"
    
    # Cache TTL (seconds)
    CACHE_TTL_PRODUCT_LIST: int = 300  # 5 minutes
    CACHE_TTL_PRODUCT_DETAIL: int = 600  # 10 minutes
    CACHE_TTL_CATEGORY_LIST: int = 3600  # 1 hour
    
    # Search
    SEARCH_MIN_QUERY_LENGTH: int = 2
    SEARCH_MAX_RESULTS: int = 50
    
    # Reviews
    MIN_RATING: int = 1
    MAX_RATING: int = 5
    REVIEW_REQUIRE_PURCHASE: bool = True

    # Cart
    CART_ITEM_MAX_QUANTITY: int = 10
    ABANDONED_CART_HOURS: int = 24
    ABANDONED_CART_EMAIL_ENABLED: bool = True

    # Flash Sales
    FLASH_SALE_MAX_ITEMS_PER_USER: int = 5
    
    # Security Validators
    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)
    
    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )
        return self
    
    @model_validator(mode="after")
    def _set_payment_return_urls(self) -> Self:
        if not self.VNPAY_RETURN_URL:
            self.VNPAY_RETURN_URL = f"{self.FRONTEND_HOST}/payment/vnpay/callback"
        return self


settings = Settings()
