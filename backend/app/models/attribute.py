from typing import TYPE_CHECKING, Optional, List
from datetime import datetime, timezone, timedelta

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import SizeTypeEnum

if TYPE_CHECKING:
    from app.models.product import ProductVariant


class ColorBase(SQLModel):
    color_name: str = Field(max_length=50, unique=True)
    color_code: str = Field(max_length=7)
    description: Optional[str] = Field(default=None, max_length=255)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class Color(ColorBase, table=True):
    __tablename__ = "colors"
    
    color_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )
    
    product_variants: List["ProductVariant"] = Relationship(back_populates="color")


class SizeBase(SQLModel):
    size_name: str = Field(max_length=20, unique=True)
    size_type: SizeTypeEnum = Field(
        sa_column=Column(PgEnum(SizeTypeEnum, name="size_type_enum", create_type=True), nullable=False)
    )
    description: Optional[str] = Field(default=None, max_length=255)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class Size(SizeBase, table=True):
    __tablename__ = "sizes"
    
    size_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )
    
    product_variants: List["ProductVariant"] = Relationship(back_populates="size")


class ColorResponse(ColorBase):
    color_id: int
    created_at: datetime
    updated_at: datetime


class SizeResponse(SizeBase):
    size_id: int
    created_at: datetime
    updated_at: datetime


class ColorCreate(ColorBase):
    pass


class ColorUpdate(SQLModel):
    color_name: Optional[str] = Field(default=None, max_length=50)
    color_code: Optional[str] = Field(default=None, max_length=7)
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class SizeCreate(SizeBase):
    pass


class SizeUpdate(SQLModel):
    size_name: Optional[str] = Field(default=None, max_length=20)
    size_type: Optional[SizeTypeEnum] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class ColorsResponse(SQLModel):
    data: List[ColorResponse]
    count: int


class SizesResponse(SQLModel):
    data: List[SizeResponse]
    count: int