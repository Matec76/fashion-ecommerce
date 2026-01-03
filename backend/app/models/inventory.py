from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional, List, Dict

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text, Index
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import InventoryChangeEnum, StockAlertTypeEnum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import ProductVariant
    from app.models.warehouse import Warehouse


class InventoryTransactionBase(SQLModel):
    variant_id: int = Field(foreign_key="product_variants.variant_id")
    transaction_type: InventoryChangeEnum = Field(
        sa_column=Column(PgEnum(InventoryChangeEnum, name="inventory_change_enum", create_type=True), nullable=False)
    )
    quantity: int = Field(description="Positive for IN, negative for OUT")
    balance_after: Optional[int] = None
    reference: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = Field(default=None, sa_column=Column(Text))


class InventoryTransaction(InventoryTransactionBase, table=True):
    __tablename__ = "inventory_transactions"
    __table_args__ = (
        Index("ix_inventory_transactions_variant_id", "variant_id"),
        Index("ix_inventory_transactions_warehouse_id", "warehouse_id"),
        Index("ix_inventory_transactions_created_at", "created_at"),
    )

    transaction_id: Optional[int] = Field(default=None, primary_key=True)
    warehouse_id: Optional[int] = Field(default=None, foreign_key="warehouses.warehouse_id")
    performed_by: Optional[int] = Field(default=None, foreign_key="users.user_id")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    variant: Optional["ProductVariant"] = Relationship(back_populates="inventory_transactions")
    warehouse: Optional["Warehouse"] = Relationship()
    user: Optional["User"] = Relationship(back_populates="inventory_transactions")


class InventoryTransactionResponse(InventoryTransactionBase):
    transaction_id: int
    warehouse_id: Optional[int]
    performed_by: Optional[int]
    created_at: datetime
    variant_summary: Optional[Dict] = None
    warehouse_summary: Optional[Dict] = None
    user_summary: Optional[Dict] = None


class InventoryTransactionCreate(SQLModel):
    variant_id: int
    warehouse_id: int
    transaction_type: InventoryChangeEnum
    quantity: int
    reference: Optional[str] = None
    note: Optional[str] = None


class InventoryBulkAdjust(SQLModel):
    """Schema for bulk inventory adjustments."""
    warehouse_id: int
    adjustments: List[dict] = Field(
        description="List of {variant_id, quantity, note}",
        min_length=1,
        max_length=100
    )
    transaction_type: InventoryChangeEnum
    reference: Optional[str] = None


class InventoryTransfer(SQLModel):
    """Schema for transferring stock between warehouses."""
    from_warehouse_id: int
    to_warehouse_id: int
    variant_id: int
    quantity: int = Field(gt=0)
    note: Optional[str] = None
    reference: Optional[str] = None


class InventoryTransactionsResponse(SQLModel):
    data: List[InventoryTransactionResponse]
    count: int


class StockAlertBase(SQLModel):
    variant_id: int = Field(foreign_key="product_variants.variant_id")
    alert_type: StockAlertTypeEnum = Field(
        sa_column=Column(PgEnum(StockAlertTypeEnum, name="stock_alert_type_enum", create_type=True), nullable=False)
    )
    threshold: int
    current_stock: int


class StockAlert(StockAlertBase, table=True):
    __tablename__ = "stock_alerts"
    __table_args__ = (
        Index("ix_stock_alerts_variant_id", "variant_id"),
        Index("ix_stock_alerts_is_resolved", "is_resolved"),
    )

    alert_id: Optional[int] = Field(default=None, primary_key=True)
    is_resolved: bool = Field(default=False)
    
    resolved_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    resolved_by: Optional[int] = Field(default=None, foreign_key="users.user_id")
    notified_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    
    notification_sent: bool = Field(default=False)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    variant: Optional["ProductVariant"] = Relationship(back_populates="stock_alerts")


class StockAlertResponse(StockAlertBase):
    alert_id: int
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    notified_at: Optional[datetime]
    notification_sent: bool
    created_at: datetime
    variant_summary: Optional[Dict] = None


class StockAlertCreate(StockAlertBase):
    pass


class StockAlertUpdate(SQLModel):
    is_resolved: Optional[bool] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None


class StockAlertsResponse(SQLModel):
    data: List[StockAlertResponse]
    count: int


class VariantStockBase(SQLModel):
    variant_id: int = Field(foreign_key="product_variants.variant_id")
    warehouse_id: int = Field(foreign_key="warehouses.warehouse_id")
    quantity: int = Field(default=0, ge=0, description="Total quantity in stock")
    reserved: int = Field(default=0, ge=0, description="Reserved for orders")


class VariantStock(VariantStockBase, table=True):
    __tablename__ = "variant_stock"
    __table_args__ = (
        Index("ix_variant_stock_variant_id", "variant_id"),
        Index("ix_variant_stock_warehouse_id", "warehouse_id"),
    )

    stock_id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    variant: Optional["ProductVariant"] = Relationship(back_populates="warehouse_stocks")
    warehouse: Optional["Warehouse"] = Relationship(back_populates="variant_stocks")

    @property
    def available(self) -> int:
        """Available quantity (total - reserved)."""
        return max(0, self.quantity - self.reserved)


class VariantStockResponse(VariantStockBase):
    stock_id: int
    available: int
    created_at: datetime
    updated_at: datetime
    variant_summary: Optional[Dict] = None
    warehouse_summary: Optional[Dict] = None


class VariantStockCreate(VariantStockBase):
    pass


class VariantStockUpdate(SQLModel):
    quantity: Optional[int] = Field(default=None, ge=0)
    reserved: Optional[int] = Field(default=None, ge=0)


class VariantStockSummary(SQLModel):
    """Summary of variant stock across all warehouses."""
    variant_id: int
    total_quantity: int
    total_reserved: int
    total_available: int
    warehouses: List[Dict]


class VariantStocksResponse(SQLModel):
    data: List[VariantStockResponse]
    count: int