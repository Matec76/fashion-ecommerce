from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Dict, Optional, Any

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import SettingTypeEnum, AdminActionEnum

if TYPE_CHECKING:
    from app.models.user import User

class SystemSettingBase(SQLModel):
    setting_key: str = Field(max_length=100, unique=True, index=True)
    setting_value: Optional[str] = Field(
        default=None, 
        sa_column=Column(Text, nullable=True)
    )
    setting_type: SettingTypeEnum = Field(
        default=SettingTypeEnum.STRING,
        sa_column=Column(PgEnum(SettingTypeEnum, name="setting_type_enum", create_type=True), nullable=False)
    )
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_public: bool = Field(default=False)

class SystemSetting(SystemSettingBase, table=True):
    __tablename__ = "system_settings"

    setting_id: Optional[int] = Field(default=None, primary_key=True)
    updated_by: Optional[int] = Field(default=None, foreign_key="users.user_id")
    
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    updater: Optional["User"] = Relationship(sa_relationship_kwargs={"lazy": "select"})

class SystemSettingResponse(SystemSettingBase):
    setting_id: int
    updated_by: Optional[int]
    updated_at: datetime

class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingUpdate(SQLModel):
    setting_value: Optional[str] = None
    setting_type: Optional[SettingTypeEnum] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class AdminActivityLogResponse(SQLModel):
    log_id: str
    user_id: int
    action_type: AdminActionEnum
    table_name: Optional[str] = None
    record_id: Optional[str] = None
    old_value: Optional[Dict] = None
    new_value: Optional[Dict] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    response_status: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    user: Optional[Dict[str, Any]] = None