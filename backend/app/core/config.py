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
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Fashion E-commerce API - Backend for modern fashion marketplace"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Algorithm for JWT
    ALGORITHM: str = "HS256"

    # CORS
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field
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

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # Email templates directory
    EMAIL_TEMPLATES_DIR: str = "app/email-templates"

    # Testing
    EMAIL_TEST_USER: EmailStr = "test@stylex.com"

    # Superuser
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_FIRSTNAME: str = "Admin"
    FIRST_SUPERUSER_LASTNAME: str = "User"

    # File Upload
    UPLOAD_DIR: str = "uploads"
    STATIC_DIR: str = "static"
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB in bytes
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    
    # Image sizes for products
    PRODUCT_IMAGE_THUMBNAIL_SIZE: tuple[int, int] = (150, 150)
    PRODUCT_IMAGE_MEDIUM_SIZE: tuple[int, int] = (500, 500)
    PRODUCT_IMAGE_LARGE_SIZE: tuple[int, int] = (1200, 1200)
    IMAGE_QUALITY: int = 85

    # Payment Gateway
    # VNPay
    VNPAY_ENABLED: bool = False
    VNPAY_TMN_CODE: str | None = None
    VNPAY_HASH_SECRET: str | None = None
    VNPAY_URL: str | None = None
    
    @computed_field
    @property
    def VNPAY_RETURN_URL(self) -> str:
        return f"{self.FRONTEND_HOST}/payment/vnpay/return"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0
    
    # Cache TTL in seconds
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_PRODUCTS: int = 600  # 10 minutes
    CACHE_TTL_CATEGORIES: int = 1800  # 30 minutes
    
    # Session
    SESSION_EXPIRE_SECONDS: int = 86400  # 24 hours

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Business Logic
    # Currency
    CURRENCY_CODE: str = "VND"
    CURRENCY_SYMBOL: str = "₫"
    
    # Tax
    TAX_RATE: float = 0.1  # 10% VAT
    TAX_ENABLED: bool = True
    
    # Shipping
    FREE_SHIPPING_THRESHOLD: int = 500000  # Free shipping above 500,000 VND
    DEFAULT_SHIPPING_FEE: int = 30000  # Default 30,000 VND
    SHIPPING_WEIGHT_UNIT: str = "kg"
    
    # Order
    ORDER_NUMBER_PREFIX: str = "FE"  # Fashion E-commerce
    ORDER_CANCELLATION_HOURS: int = 24  # Can cancel within 24 hours
    ORDER_AUTO_COMPLETE_DAYS: int = 7  # Auto complete 7 days after delivery
    
    # Return/Refund
    RETURN_WINDOW_DAYS: int = 7  # Can return within 7 days
    REFUND_PROCESSING_DAYS: int = 3  # Process refund within 3 days
    
    # Cart
    CART_ITEM_MAX_QUANTITY: int = 99
    CART_EXPIRY_DAYS: int = 30  # Guest cart expires after 30 days
    ABANDONED_CART_HOURS: int = 24  # Cart abandoned after 24 hours
    ABANDONED_CART_EMAIL_DELAY_HOURS: int = 2  # Send recovery email after 2 hours
    MAX_ABANDONED_CART_EMAILS: int = 3
    STOCK_RESERVE_MINUTES: int = 15  # Reserve stock during checkout

    # Loyalty Points
    LOYALTY_ENABLED: bool = True
    POINTS_PER_CURRENCY: int = 1000  # 1 point per 1,000 VND spent
    POINTS_FOR_REVIEW: int = 10
    POINTS_FOR_REVIEW_WITH_IMAGE: int = 20
    POINTS_FOR_REFERRAL: int = 100
    POINTS_EXPIRY_DAYS: int = 365  # Points expire after 1 year
    MIN_POINTS_TO_REDEEM: int = 100
    POINTS_TO_CURRENCY_RATE: int = 1000  # 1 point = 1,000 VND discount

    # Review
    REVIEW_MIN_RATING: int = 1
    REVIEW_MAX_RATING: int = 5
    REVIEW_MAX_IMAGES: int = 5
    REVIEW_AUTO_APPROVE: bool = False  # Require admin approval
    REVIEW_EDIT_WINDOW_HOURS: int = 24  # Can edit review within 24 hours

    # Inventory
    LOW_STOCK_THRESHOLD: int = 5
    ENABLE_BACKORDER: bool = False
    ENABLE_STOCK_NOTIFICATIONS: bool = True

    # Coupon
    COUPON_CODE_LENGTH: int = 8
    MAX_COUPON_USAGE_PER_USER: int = 1

    # Product
    FEATURED_PRODUCTS_LIMIT: int = 12
    NEW_ARRIVALS_DAYS: int = 30  # Products from last 30 days
    RELATED_PRODUCTS_LIMIT: int = 8
    PRODUCT_SLUG_MAX_LENGTH: int = 255

    # Search
    SEARCH_MIN_QUERY_LENGTH: int = 2
    SEARCH_RESULTS_LIMIT: int = 50
    POPULAR_SEARCHES_LIMIT: int = 10

    # Analytics
    TRACK_PRODUCT_VIEWS: bool = True
    TRACK_SEARCH_QUERIES: bool = True
    ANALYTICS_RETENTION_DAYS: int = 90

    # Notification
    NOTIFICATION_RETENTION_DAYS: int = 30
    MAX_NOTIFICATIONS_PER_USER: int = 100

    # Admin
    ADMIN_ACTIVITY_LOG_RETENTION_DAYS: int = 365
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Feature Flags
    FEATURE_WISHLIST: bool = True
    FEATURE_REVIEWS: bool = True
    FEATURE_LOYALTY_POINTS: bool = True
    FEATURE_FLASH_SALES: bool = True
    FEATURE_COUPONS: bool = True
    FEATURE_PRODUCT_QA: bool = True
    FEATURE_NOTIFICATIONS: bool = True
    FEATURE_ABANDONED_CART_RECOVERY: bool = True
    FEATURE_REFERRAL_PROGRAM: bool = False

    # Monitoring
    SENTRY_DSN: HttpUrl | None = None
    
    @computed_field
    @property
    def sentry_enabled(self) -> bool:
        return bool(self.SENTRY_DSN)
    
    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

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
        
        if self.ENVIRONMENT == "production":
            if self.VNPAY_ENABLED:
                if not self.VNPAY_TMN_CODE or not self.VNPAY_HASH_SECRET:
                    raise ValueError(
                        "VNPay is enabled but credentials are not properly configured"
                    )
        return self


settings = Settings()
