from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text, JSON
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import NotificationTypeEnum, EmailTypeEnum, EmailStatusEnum

if TYPE_CHECKING:
    from app.models.user import User


class NotificationBase(SQLModel):
    notification_type: NotificationTypeEnum = Field(
        sa_column=Column(PgEnum(NotificationTypeEnum, name="notification_type_enum", create_type=True), nullable=False)
    )
    title: str = Field(max_length=255)
    message: Optional[str] = Field(default=None, sa_column=Column(Text))
    reference_id: Optional[int] = Field(default=None)

class Notification(NotificationBase, table=True):
    __tablename__ = "notifications"

    notification_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    is_read: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    read_at: Optional[datetime] = None

    user: Optional["User"] = Relationship(back_populates="notifications")


class NotificationResponse(NotificationBase):
    notification_id: int
    user_id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationBulkCreate(NotificationBase):
    user_ids: List[int] = Field(min_length=1, max_length=1000)


class NotificationUpdate(SQLModel):
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None


class NotificationsResponse(SQLModel):
    data: List[NotificationResponse]
    count: int
    unread_count: int = 0


class NotificationPreferencesBase(SQLModel):
    email_notifications: bool = Field(default=True)
    push_notifications: bool = Field(default=True)
    order_updates: bool = Field(default=True)
    promotions: bool = Field(default=True)
    product_back_in_stock: bool = Field(default=True)
    review_responses: bool = Field(default=True)
    system_announcements: bool = Field(default=True)


class NotificationPreferences(NotificationPreferencesBase, table=True):
    __tablename__ = "notification_preferences"

    preference_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id", unique=True)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )


class NotificationPreferencesResponse(NotificationPreferencesBase):
    preference_id: int
    user_id: int
    updated_at: datetime


class NotificationPreferencesUpdate(NotificationPreferencesBase):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    order_updates: Optional[bool] = None
    promotions: Optional[bool] = None
    product_back_in_stock: Optional[bool] = None
    review_responses: Optional[bool] = None
    system_announcements: Optional[bool] = None


class EmailQueueBase(SQLModel):
    recipient_email: str = Field(max_length=255)
    email_type: EmailTypeEnum = Field(
        sa_column=Column(PgEnum(EmailTypeEnum, name="email_type_enum", create_type=True), nullable=False)
    )
    subject: str = Field(max_length=500)
    html_body: Optional[str] = Field(default=None, sa_column=Column(Text))
    context: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    scheduled_at: Optional[datetime] = None
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=0)
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))


class EmailQueue(EmailQueueBase, table=True):
    __tablename__ = "email_queue"

    email_id: Optional[int] = Field(default=None, primary_key=True)
    status: EmailStatusEnum = Field(
        default=EmailStatusEnum.PENDING,
        sa_column=Column(PgEnum(EmailStatusEnum, name="email_status_enum", create_type=True), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    sent_at: Optional[datetime] = None


class EmailQueueResponse(EmailQueueBase):
    email_id: int
    status: EmailStatusEnum
    created_at: datetime
    sent_at: Optional[datetime]


class EmailQueueCreate(SQLModel):
    recipient_email: str = Field(max_length=255)
    email_type: EmailTypeEnum
    subject: str = Field(max_length=500)
    html_body: Optional[str] = None
    context: Optional[dict] = None
    scheduled_at: Optional[datetime] = None


class EmailQueueUpdate(SQLModel):
    status: Optional[EmailStatusEnum] = None
    retry_count: Optional[int] = Field(default=None, ge=0)
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None


class EmailQueuesResponse(SQLModel):
    data: List[EmailQueueResponse]
    count: int