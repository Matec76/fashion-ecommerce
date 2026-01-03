from decimal import Decimal
import warnings
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    HttpUrl,
    PostgresDsn,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    """Parse CORS origins from string or list."""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(f"Invalid CORS format: {v}")


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Fashion E-commerce API - Backend for modern fashion marketplace"
    
    FRONTEND_HOST: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "http://localhost:8080"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        """Get all CORS origins including frontend."""
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]
    
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY strength."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        if v == "changethis":
            raise ValueError("SECRET_KEY must be changed from default value")
        return v
    
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        """Build PostgreSQL database URI."""
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )
    
    MONGO_DATABASE_URI: str
    MONGO_DATABASE_NAME: str
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    
    @computed_field
    @property
    def REDIS_URL(self) -> str:
        """Build Redis connection URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-southeast-1"
    AWS_S3_BUCKET: str = ""
    
    S3_CATEGORIES_IMAGES_FOLDER: str = "categories"
    S3_COLLECTIONS_IMAGES_FOLDER: str = "collections"
    S3_PRODUCT_IMAGES_FOLDER: str = "products"
    S3_USER_AVATARS_FOLDER: str = "avatars"
    S3_BANNERS_FOLDER: str = "banners"
    S3_REVIEWS_FOLDER: str = "reviews"
    
    CDN_URL: str = ""
    
    @computed_field
    @property
    def s3_enabled(self) -> bool:
        """Check if S3 is properly configured."""
        return bool(
            self.AWS_ACCESS_KEY_ID 
            and self.AWS_SECRET_ACCESS_KEY 
            and self.AWS_S3_BUCKET
        )
    
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
        """Set default email from name if not provided."""
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        """Check if email is properly configured."""
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    EMAIL_TEMPLATES_DIR: str = str(Path("app") / "templates" / "emails")
    EMAIL_TEST_USER: EmailStr = "test@stylex.com"
    
    @field_validator("EMAIL_TEMPLATES_DIR")
    @classmethod
    def validate_templates_dir(cls, v: str) -> str:
        """Validate email templates directory exists."""
        path = Path(v)
        if not path.exists():
            warnings.warn(
                f"Email templates directory does not exist: {v}",
                stacklevel=2
            )
        return v
    
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str
    FIRST_SUPERUSER_FIRSTNAME: str = "Admin"
    FIRST_SUPERUSER_LASTNAME: str = "User"
    
    @field_validator("FIRST_SUPERUSER_PASSWORD")
    @classmethod
    def validate_superuser_password(cls, v: str, info) -> str:
        """Validate superuser password strength."""
        if info.data.get("ENVIRONMENT") != "local" and v == "changethis":
            raise ValueError(
                "FIRST_SUPERUSER_PASSWORD must be changed from default in "
                "staging/production environments"
            )
        if len(v) < 8:
            raise ValueError("FIRST_SUPERUSER_PASSWORD must be at least 8 characters")
        return v
    
    UPLOAD_DIR: str = "uploads"
    STATIC_DIR: str = "static"
    MAX_UPLOAD_SIZE: int = 10485760
    ALLOWED_IMAGE_TYPES: list[str] = [
        "image/jpeg", 
        "image/png", 
        "image/webp", 
        "image/jpg",
        "image/gif"
    ]

    @field_validator("UPLOAD_DIR", "STATIC_DIR")
    @classmethod
    def validate_directories(cls, v: str) -> str:
        """Ensure upload directories exist."""
        path = Path(v)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                warnings.warn(
                    f"Could not create directory {v}: {e}",
                    stacklevel=2
                )
        return v
    
    PAYOS_ENABLED: bool = False
    PAYOS_CLIENT_ID: str = ""
    PAYOS_API_KEY: str = ""
    PAYOS_CHECKSUM_KEY: str = ""
    PAYOS_RETURN_URL: str = ""
    PAYOS_CANCEL_URL: str = ""
    
    @computed_field
    @property
    def PAYOS_RETURN_URL_COMPUTED(self) -> str:
        """Get PayOS return URL with fallback."""
        return self.PAYOS_RETURN_URL or f"{self.FRONTEND_HOST}/payment/success"
    
    @computed_field
    @property
    def PAYOS_CANCEL_URL_COMPUTED(self) -> str:
        """Get PayOS cancel URL with fallback."""
        return self.PAYOS_CANCEL_URL or f"{self.FRONTEND_HOST}/payment/cancel"
    
    @computed_field
    @property
    def payos_configured(self) -> bool:
        """Check if PayOS is properly configured."""
        return bool(
            self.PAYOS_ENABLED
            and self.PAYOS_CLIENT_ID
            and self.PAYOS_API_KEY
            and self.PAYOS_CHECKSUM_KEY
        )
    
    GOOGLE_API_KEY: str = "" 
    GOOGLE_MODEL: str = "gemini-2.0-flash-exp"
    
    @computed_field
    @property
    def ai_enabled(self) -> bool:
        return bool(self.GOOGLE_API_KEY)
    
    # Page
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    @field_validator("MAX_PAGE_SIZE")
    @classmethod
    def validate_max_page_size(cls, v: int) -> int:
        """Ensure max page size is reasonable."""
        if v > 1000:
            warnings.warn(
                f"MAX_PAGE_SIZE {v} is very large, consider reducing it",
                stacklevel=2
            )
        return v
    
    ORDER_NUMBER_PREFIX: str = "ORD"
    
    PAYMENT_MAX_RETRY_AGE_DAYS: int = 30
    PAYMENT_TIMEOUT_MINUTES: int = 15
    PAYMENT_MAX_REFUND_AMOUNT_PER_ADMIN: Decimal = Decimal("10000000")
    PAYMENT_WEBHOOK_LOCK_TIMEOUT: int = 30
    PAYMENT_WEBHOOK_RATE_LIMIT_WINDOW: int = 60
    PAYMENT_WEBHOOK_RATE_LIMIT_MAX: int = 100
    
    
    SENTRY_DSN: HttpUrl | None = None
    
    @computed_field
    @property
    def sentry_enabled(self) -> bool:
        """Check if Sentry is configured."""
        return bool(self.SENTRY_DSN)
    
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    
    @model_validator(mode="after")
    def _validate_production_settings(self) -> Self:
        """Validate critical settings for production environment."""
        if self.ENVIRONMENT == "production":
            if not self.POSTGRES_PASSWORD or self.POSTGRES_PASSWORD == "changethis":
                raise ValueError(
                    "POSTGRES_PASSWORD must be set and changed from default "
                    "in production environment"
                )
            
            if self.PAYOS_ENABLED:
                if not self.payos_configured:
                    raise ValueError(
                        "PayOS is enabled but credentials are not properly configured. "
                        "Set PAYOS_CLIENT_ID, PAYOS_API_KEY, and PAYOS_CHECKSUM_KEY."
                    )
            
            if not self.emails_enabled:
                warnings.warn(
                    "Email is not configured in production. "
                    "Some features may not work properly.",
                    stacklevel=1
                )
            
            if not self.s3_enabled:
                warnings.warn(
                    "S3 is not configured. File uploads will be stored locally.",
                    stacklevel=1
                )
        
        return self


settings = Settings()


__all__ = ["settings", "Settings"]