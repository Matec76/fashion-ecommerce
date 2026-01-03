from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text

if TYPE_CHECKING:
    from app.models.inventory import VariantStock


class WarehouseBase(SQLModel):
    warehouse_name: str = Field(max_length=100)
    address: Optional[str] = Field(default=None, sa_column=Column(Text))
    city: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)


class Warehouse(WarehouseBase, table=True):
    __tablename__ = "warehouses"

    warehouse_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    variant_stocks: List["VariantStock"] = Relationship(back_populates="warehouse", cascade_delete=True)


class WarehouseResponse(WarehouseBase):
    warehouse_id: int
    created_at: datetime
    updated_at: datetime


class WarehouseDetailResponse(WarehouseResponse):
    total_variants: int = 0
    total_quantity: int = 0
    total_reserved: int = 0
    total_available: int = 0


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(SQLModel):
    warehouse_name: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class WarehousesResponse(SQLModel):
    data: List[WarehouseResponse]
    count: int