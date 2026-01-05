from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List, Dict, Any

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import Numeric, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB

from app.models.enums import PaymentStatusEnum

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.payment_method import PaymentMethod
    from app.models.return_refund import RefundTransaction


class PaymentTransactionBase(SQLModel):
    order_id: int = Field(foreign_key="orders.order_id")
    payment_method_id: Optional[int] = Field(default=None, foreign_key="payment_methods.payment_method_id")
    
    transaction_code: str = Field(
        max_length=255, 
        unique=True, 
        index=True
    )
    
    gateway_transaction_id: Optional[str] = Field(
        default=None,
        max_length=255,
        index=True
    )
    
    payment_gateway: Optional[str] = Field(default=None, max_length=50)
    
    amount: Decimal = Field(sa_column=Column(Numeric(18, 2)), ge=0)
    
    status: PaymentStatusEnum = Field(
        default=PaymentStatusEnum.PENDING,
        sa_column=Column(PgEnum(PaymentStatusEnum, name="payment_status_enum", create_type=True), nullable=False)
    )
    
    payment_url: Optional[str] = Field(default=None, sa_column=Column(Text))
    qr_code: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    gateway_response: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    payment_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))


class PaymentTransaction(PaymentTransactionBase, table=True):
    __tablename__ = "payment_transactions"

    transaction_id: Optional[int] = Field(default=None, primary_key=True)
    
    paid_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    order: Optional["Order"] = Relationship(back_populates="payment_transactions")
    payment_method: Optional["PaymentMethod"] = Relationship(back_populates="transactions")
    refunds: List["RefundTransaction"] = Relationship(back_populates="payment_transaction")


class PaymentTransactionResponse(PaymentTransactionBase):
    transaction_id: int
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaymentTransactionCreate(PaymentTransactionBase):
    pass


class PaymentTransactionUpdate(SQLModel):
    transaction_code: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    payment_method_id: Optional[int] = None
    payment_gateway: Optional[str] = None
    amount: Optional[Decimal] = None
    status: Optional[PaymentStatusEnum] = None
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    notes: Optional[str] = None
    gateway_response: Optional[str] = None
    payment_metadata: Optional[Dict[str, Any]] = None
    paid_at: Optional[datetime] = None


class PaymentTransactionsResponse(SQLModel):
    data: List[PaymentTransactionResponse]
    count: int


class PaymentResponseInfo(SQLModel):
    payment_method: str
    transaction_id: int
    message: str
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    payment_instructions: Optional[str] = None
    bank_info: Optional[Dict[str, Any]] = None


class PaymentRetryResponse(SQLModel):
    success: bool
    message: str
    payment_url: Optional[str] = None
    transaction_id: Optional[int] = None


class PaymentStatistics(SQLModel):
    total_transactions: int
    successful_payments: int
    failed_payments: int
    pending_payments: int
    total_amount: Decimal
    total_paid: Decimal
    success_rate: float
    gateway_breakdown: dict


class RefundRequest(SQLModel):
    transaction_id: int
    refund_amount: Decimal
    reason: str
    notes: Optional[str] = None


class RefundResponse(SQLModel):
    refund_id: int
    transaction_id: int
    refund_amount: Decimal
    status: str
    created_at: datetime