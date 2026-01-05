from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text, Numeric
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB

from app.models.enums import (
    ReturnReasonEnum,
    ReturnStatusEnum,
    RefundMethodEnum,
    ItemConditionEnum
)

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order
    from app.models.product import Product, ProductVariant
    from app.models.payment import PaymentTransaction


class RefundTransactionBase(SQLModel):
    return_id: int = Field(foreign_key="return_requests.return_id")
    payment_transaction_id: Optional[int] = Field(default=None, foreign_key="payment_transactions.transaction_id")
    refund_amount: Decimal = Field(sa_column=Column(Numeric(18, 2)))
    refund_method: RefundMethodEnum = Field(
        default=RefundMethodEnum.ORIGINAL_PAYMENT,
        sa_column=Column(PgEnum(RefundMethodEnum, name="refund_method_enum", create_type=True), nullable=False)
    )
    status: str = Field(default="pending", max_length=50)
    gateway_response: Optional[str] = Field(default=None, sa_column=Column(Text))
    initiated_by: Optional[int] = Field(default=None, foreign_key="users.user_id")


class RefundTransaction(RefundTransactionBase, table=True):
    __tablename__ = "refund_transactions"

    refund_id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    processed_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=True)))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    return_request: Optional["ReturnRequest"] = Relationship(back_populates="refunds")
    payment_transaction: Optional["PaymentTransaction"] = Relationship(back_populates="refunds")
    initiator: Optional["User"] = Relationship()


class RefundTransactionCreate(RefundTransactionBase):
    pass


class RefundTransactionUpdate(SQLModel):
    status: Optional[str] = Field(default=None, max_length=50)
    gateway_response: Optional[str] = None
    processed_at: Optional[datetime] = None


class RefundTransactionResponse(RefundTransactionBase):
    refund_id: int
    created_at: datetime
    processed_at: Optional[datetime]
    updated_at: datetime


class RefundTransactionsResponse(SQLModel):
    data: List[RefundTransactionResponse]
    count: int


class ReturnRequestBase(SQLModel):
    order_id: int = Field(foreign_key="orders.order_id")
    user_id: int = Field(foreign_key="users.user_id")
    return_reason: ReturnReasonEnum = Field(
        sa_column=Column(PgEnum(ReturnReasonEnum, name="return_reason_enum", create_type=True), nullable=False)
    )
    reason_detail: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: ReturnStatusEnum = Field(
        default=ReturnStatusEnum.PENDING,
        sa_column=Column(PgEnum(ReturnStatusEnum, name="return_status_enum", create_type=True), nullable=False)
    )
    refund_amount: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 2)))
    refund_method: Optional[RefundMethodEnum] = Field(
        default=None,
        sa_column=Column(PgEnum(RefundMethodEnum, name="refund_method_enum", create_type=True), nullable=True)
    )
    images: Optional[List[str]] = Field(default=None, sa_column=Column(JSONB))


class ReturnRequest(ReturnRequestBase, table=True):
    __tablename__ = "return_requests"

    return_id: Optional[int] = Field(default=None, primary_key=True)
    
    processed_note: Optional[str] = Field(default=None, sa_column=Column(Text))
    processed_by: Optional[int] = Field(default=None, foreign_key="users.user_id")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )
    completed_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=True)))

    user: Optional["User"] = Relationship(
        back_populates="return_requests",
        sa_relationship_kwargs={"foreign_keys": "[ReturnRequest.user_id]"}
    )
    processor: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ReturnRequest.processed_by]"}
    )
    
    order: Optional["Order"] = Relationship(back_populates="return_requests")
    items: List["ReturnItem"] = Relationship(back_populates="return_request", cascade_delete=True)
    refunds: List["RefundTransaction"] = Relationship(back_populates="return_request", cascade_delete=True)


class ReturnItemBase(SQLModel):
    product_id: int = Field(foreign_key="products.product_id")
    variant_id: Optional[int] = Field(default=None, foreign_key="product_variants.variant_id")
    quantity: int = Field(ge=1)
    condition: ItemConditionEnum = Field(
        default=ItemConditionEnum.UNOPENED,
        sa_column=Column(PgEnum(ItemConditionEnum, name="item_condition_enum", create_type=True), nullable=False)
    )
    note: Optional[str] = Field(default=None, sa_column=Column(Text))


class ReturnItem(ReturnItemBase, table=True):
    __tablename__ = "return_items"

    return_item_id: Optional[int] = Field(default=None, primary_key=True)
    return_id: int = Field(foreign_key="return_requests.return_id")
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    return_request: Optional["ReturnRequest"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship(back_populates="return_items")
    variant: Optional["ProductVariant"] = Relationship(back_populates="return_items")


class ReturnItemCreate(SQLModel):
    product_id: int
    variant_id: int
    quantity: int
    condition: ItemConditionEnum = ItemConditionEnum.UNOPENED
    note: Optional[str] = None


class ReturnItemResponse(ReturnItemBase):
    return_item_id: int
    return_id: int
    created_at: datetime


class ReturnItemUpdate(SQLModel):
    quantity: Optional[int] = Field(default=None, ge=1)
    condition: Optional[ItemConditionEnum] = None
    note: Optional[str] = None


class ReturnRequestCreate(SQLModel):
    order_id: int
    return_reason: ReturnReasonEnum
    reason_detail: Optional[str] = None
    images: Optional[List[str]] = None
    refund_method: RefundMethodEnum
    items: List[ReturnItemCreate]


class ReturnRequestUpdate(SQLModel):
    status: Optional[ReturnStatusEnum] = None
    reason_detail: Optional[str] = None
    refund_amount: Optional[Decimal] = None
    refund_method: Optional[RefundMethodEnum] = None
    images: Optional[List[str]] = None
    processed_by: Optional[int] = None
    processed_note: Optional[str] = None
    completed_at: Optional[datetime] = None


class ReturnRequestResponse(ReturnRequestBase):
    return_id: int
    processed_note: Optional[str]
    processed_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    items: List[ReturnItemResponse] = []
    refunds: List[RefundTransactionResponse] = []


class ReturnRequestsResponse(SQLModel):
    data: List[ReturnRequestResponse]
    count: int


class ReturnRequestApprove(SQLModel):
    refund_amount: Decimal
    refund_method: RefundMethodEnum
    processed_note: Optional[str] = None


class ReturnRequestReject(SQLModel):
    processed_note: str