from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import Numeric, text
from pydantic import field_validator

from app.models.enums import ProcessingFeeType

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.payment import PaymentTransaction


class PaymentMethodBase(SQLModel):
    method_code: str = Field(max_length=50, unique=True, index=True)
    method_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    icon_url: Optional[str] = Field(default=None, max_length=500)
    
    processing_fee: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(18, 2)), ge=0)
    processing_fee_type: str = Field(default=ProcessingFeeType.FIXED.value, max_length=20)
    
    min_order_amount: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 2)))
    max_order_amount: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 2)))
    
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0)

    @field_validator('processing_fee_type')
    @classmethod
    def validate_fee_type(cls, v: str) -> str:
        allowed_types = [ProcessingFeeType.FIXED.value, ProcessingFeeType.PERCENTAGE.value]
        if v not in allowed_types:
            raise ValueError(f"processing_fee_type must be one of: {', '.join(allowed_types)}")
        return v

    @field_validator('max_order_amount')
    @classmethod
    def validate_order_amounts(cls, v: Optional[Decimal], info) -> Optional[Decimal]:
        if v is not None and info.data.get('min_order_amount') is not None:
            if v <= info.data['min_order_amount']:
                raise ValueError('max_order_amount must be greater than min_order_amount')
        return v


class PaymentMethod(PaymentMethodBase, table=True):
    __tablename__ = "payment_methods"

    payment_method_id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    orders: List["Order"] = Relationship(back_populates="payment_method")
    transactions: List["PaymentTransaction"] = Relationship(back_populates="payment_method")


class PaymentMethodResponse(PaymentMethodBase):
    payment_method_id: int
    created_at: datetime
    updated_at: datetime


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(SQLModel):
    method_code: Optional[str] = Field(default=None, max_length=50)
    method_name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    icon_url: Optional[str] = Field(default=None, max_length=500)
    processing_fee: Optional[Decimal] = Field(default=None, ge=0)
    processing_fee_type: Optional[str] = Field(default=None, max_length=20)
    min_order_amount: Optional[Decimal] = None
    max_order_amount: Optional[Decimal] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

    @field_validator('processing_fee_type')
    @classmethod
    def validate_fee_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_types = [ProcessingFeeType.FIXED.value, ProcessingFeeType.PERCENTAGE.value]
            if v not in allowed_types:
                raise ValueError(f"processing_fee_type must be one of: {', '.join(allowed_types)}")
        return v


class PaymentMethodsResponse(SQLModel):
    data: List[PaymentMethodResponse]
    count: int


class PaymentMethodStatistics(SQLModel):
    payment_method_id: int
    method_name: str
    total_transactions: int
    successful_transactions: int
    failed_transactions: int
    total_amount: Decimal
    success_rate: float