from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import Numeric, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB

from app.models.enums import OrderStatusEnum, PaymentStatusEnum
from app.models.payment import PaymentResponseInfo

if TYPE_CHECKING:
    from app.models.product import ProductVariant
    from app.models.user import User
    from app.models.payment import PaymentTransaction, PaymentTransactionResponse
    from app.models.payment_method import PaymentMethod
    from app.models.coupon import OrderCoupon, OrderCouponResponse
    from app.models.loyalty import PointTransaction
    from app.models.return_refund import ReturnRequest


class ShippingMethodBase(SQLModel):
    method_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    base_cost: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(18, 2)), ge=0)
    estimated_days: Optional[str] = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)


class ShippingMethod(ShippingMethodBase, table=True):
    __tablename__ = "shipping_methods"

    shipping_method_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    orders: List["Order"] = Relationship(back_populates="shipping_method")


class ShippingMethodResponse(ShippingMethodBase):
    shipping_method_id: int
    created_at: datetime
    updated_at: datetime


class ShippingMethodCreate(ShippingMethodBase):
    pass


class ShippingMethodUpdate(SQLModel):
    method_name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    base_cost: Optional[Decimal] = Field(default=None, ge=0)
    estimated_days: Optional[str] = Field(default=None, max_length=50)
    is_active: Optional[bool] = None


class ShippingMethodsResponse(SQLModel):
    data: List[ShippingMethodResponse]
    count: int


class OrderBase(SQLModel):
    user_id: int = Field(foreign_key="users.user_id")
    order_number: str = Field(max_length=50, unique=True, index=True)
    
    order_status: OrderStatusEnum = Field(
        default=OrderStatusEnum.PENDING,
        sa_column=Column(PgEnum(OrderStatusEnum, name="order_status_enum", create_type=False), nullable=False)
    )
    payment_status: PaymentStatusEnum = Field(
        default=PaymentStatusEnum.PENDING,
        sa_column=Column(PgEnum(PaymentStatusEnum, name="payment_status_enum", create_type=False), nullable=False)
    )
    payment_method_id: Optional[int] = Field(
        default=None,
        foreign_key="payment_methods.payment_method_id"
    )
    
    subtotal: Decimal = Field(sa_column=Column(Numeric(18, 2)), default=Decimal("0.00"), ge=0)
    shipping_fee: Decimal = Field(sa_column=Column(Numeric(18, 2)), default=Decimal("0.00"), ge=0)
    discount_amount: Decimal = Field(sa_column=Column(Numeric(18, 2)), default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(sa_column=Column(Numeric(18, 2)), default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(sa_column=Column(Numeric(18, 2)), default=Decimal("0.00"), ge=0)
    
    shipping_method_id: Optional[int] = Field(default=None, foreign_key="shipping_methods.shipping_method_id")
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    shipping_snapshot: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    billing_snapshot: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))


class Order(OrderBase, table=True):
    __tablename__ = "orders"

    order_id: Optional[int] = Field(default=None, primary_key=True)
    
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    carrier: Optional[str] = Field(default=None, max_length=50)
    estimated_delivery: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    delivered_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    
    cancellation_reason: Optional[str] = Field(default=None, sa_column=Column(Text))
    cancelled_by: Optional[int] = Field(default=None, foreign_key="users.user_id")
    
    user_snapshot: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    order_ip: Optional[str] = Field(default=None, max_length=45)
    order_device: Optional[str] = Field(default=None, max_length=255)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    user: Optional["User"] = Relationship(
        back_populates="orders",
        sa_relationship_kwargs={"foreign_keys": "[Order.user_id]"}
    )
    
    cancelled_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Order.cancelled_by]",
            "primaryjoin": "Order.cancelled_by==User.user_id"
        }
    )

    shipping_method: Optional["ShippingMethod"] = Relationship(back_populates="orders")
    items: List["OrderItem"] = Relationship(back_populates="order", cascade_delete=True)
    status_history: List["OrderStatusHistory"] = Relationship(back_populates="order", cascade_delete=True)
    
    payment_method: Optional["PaymentMethod"] = Relationship(back_populates="orders")
    payment_transactions: List["PaymentTransaction"] = Relationship(back_populates="order", cascade_delete=True)
    order_coupons: List["OrderCoupon"] = Relationship(back_populates="order", cascade_delete=True)
    point_transactions: List["PointTransaction"] = Relationship(back_populates="order")
    return_requests: List["ReturnRequest"] = Relationship(back_populates="order")


class OrderResponse(OrderBase):
    order_id: int
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class OrderCreate(SQLModel):
    shipping_address_id: int
    billing_address_id: Optional[int] = None
    shipping_method_id: int = 1
    payment_method_id: int
    notes: Optional[str] = None
    coupon_code: Optional[str] = None


class OrderUpdate(SQLModel):
    order_status: Optional[OrderStatusEnum] = None
    payment_status: Optional[PaymentStatusEnum] = None
    payment_method_id: Optional[int] = None
    shipping_fee: Optional[Decimal] = Field(default=None, ge=0)
    discount_amount: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    shipping_method_id: Optional[int] = None
    tracking_number: Optional[str] = Field(default=None, max_length=100)
    carrier: Optional[str] = Field(default=None, max_length=50)
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[int] = None
    notes: Optional[str] = None
    shipping_snapshot: Optional[Dict[str, Any]] = None
    billing_snapshot: Optional[Dict[str, Any]] = None


class OrderStatusUpdate(SQLModel):
    order_status: OrderStatusEnum
    comment: Optional[str] = None


class OrdersResponse(SQLModel):
    data: List[OrderResponse]
    count: int


class OrderItemBase(SQLModel):
    order_id: int = Field(foreign_key="orders.order_id")
    variant_id: int = Field(foreign_key="product_variants.variant_id")
    
    product_name: str = Field(max_length=255)
    sku: Optional[str] = Field(default=None, max_length=100)
    color: Optional[str] = Field(default=None, max_length=50)
    size: Optional[str] = Field(default=None, max_length=20)
    
    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(sa_column=Column(Numeric(18, 2)), ge=0)
    subtotal: Decimal = Field(sa_column=Column(Numeric(18, 2)), ge=0)


class OrderItem(OrderItemBase, table=True):
    __tablename__ = "order_items"

    order_item_id: Optional[int] = Field(default=None, primary_key=True)

    order: Optional["Order"] = Relationship(back_populates="items")
    variant: Optional["ProductVariant"] = Relationship(back_populates="order_items")


class OrderItemResponse(OrderItemBase):
    order_item_id: int


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(SQLModel):
    quantity: Optional[int] = Field(default=None, ge=1)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    subtotal: Optional[Decimal] = Field(default=None, ge=0)


class OrderItemsResponse(SQLModel):
    data: List[OrderItemResponse]
    count: int


class OrderStatusHistoryBase(SQLModel):
    order_id: int = Field(foreign_key="orders.order_id")
    old_status: Optional[str] = Field(default=None, max_length=50)
    new_status: str = Field(max_length=50)
    comment: Optional[str] = Field(default=None, sa_column=Column(Text))
    changed_by: Optional[int] = Field(default=None, foreign_key="users.user_id")


class OrderStatusHistory(OrderStatusHistoryBase, table=True):
    __tablename__ = "order_status_history"

    history_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    order: Optional["Order"] = Relationship(back_populates="status_history")


class OrderStatusHistoryResponse(OrderStatusHistoryBase):
    history_id: int
    created_at: datetime


class OrderStatusHistoryCreate(OrderStatusHistoryBase):
    pass


class OrderStatusHistoriesResponse(SQLModel):
    data: List[OrderStatusHistoryResponse]
    count: int


class OrderDetailResponse(OrderResponse):
    items: List[OrderItemResponse] = []
    status_history: List[OrderStatusHistoryResponse] = []
    payment_transactions: List["PaymentTransactionResponse"] = []
    order_coupons: List["OrderCouponResponse"] = []
    shipping_method: Optional[ShippingMethodResponse] = None


class OrderStatistics(SQLModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    shipped_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: Decimal


class OrderCreationResponse(SQLModel):
    order: OrderDetailResponse
    payment: PaymentResponseInfo


from app.models.payment import PaymentTransactionResponse
from app.models.coupon import OrderCouponResponse

OrderDetailResponse.model_rebuild()
OrderCreationResponse.model_rebuild()