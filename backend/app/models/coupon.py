from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import Numeric, text, Index
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from pydantic import model_validator

from app.models.enums import DiscountTypeEnum
from app.models.product import ProductImageResponse

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.product import Product
    from app.models.category import Category


class CouponBase(SQLModel):
    coupon_code: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    discount_type: DiscountTypeEnum = Field(
        sa_column=Column(PgEnum(DiscountTypeEnum, name="discount_type_enum", create_type=True), nullable=False)
    )
    discount_value: Decimal = Field(sa_column=Column(Numeric(10, 2)), ge=0)
    min_purchase_amount: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)), ge=0)
    max_discount_amount: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(10, 2)))
    usage_limit: Optional[int] = Field(default=None, gt=0)
    used_count: int = Field(default=0, ge=0)
    start_date: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(TIMESTAMP(timezone=True), index=True)
    )
    end_date: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(TIMESTAMP(timezone=True), index=True)
    )
    is_active: bool = Field(default=True)
    category_id: Optional[int] = Field(default=None, foreign_key="categories.category_id", nullable=True)
    free_shipping: bool = Field(default=False)
    min_items: Optional[int] = Field(default=None, nullable=True)
    customer_eligibility: Optional[str] = Field(default="ALL", max_length=50)

    @model_validator(mode='after')
    def validate_coupon_fields(self):
        if self.discount_type == DiscountTypeEnum.PERCENTAGE:
            if self.discount_value > 100:
                raise ValueError('Percentage discount cannot exceed 100%')
        
        if self.end_date is not None and self.start_date is not None:
            if self.end_date <= self.start_date:
                raise ValueError('end_date must be after start_date')
        
        return self


class Coupon(CouponBase, table=True):
    __tablename__ = "coupons"
    
    __table_args__ = (
        Index('idx_coupon_active_dates', 'is_active', 'start_date', 'end_date'),
    )

    coupon_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    category: Optional["Category"] = Relationship(back_populates="coupons")
    order_coupons: List["OrderCoupon"] = Relationship(back_populates="coupon", cascade_delete=True)


class CouponResponse(CouponBase):
    coupon_id: int
    created_at: datetime


class CouponCreate(CouponBase):
    pass


class CouponUpdate(SQLModel):
    coupon_code: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    discount_type: Optional[DiscountTypeEnum] = None
    discount_value: Optional[Decimal] = Field(default=None, ge=0)
    min_purchase_amount: Optional[Decimal] = Field(default=None, ge=0)
    max_discount_amount: Optional[Decimal] = Field(default=None, ge=0)
    usage_limit: Optional[int] = Field(default=None, gt=0)
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    category_id: Optional[int] = None
    free_shipping: Optional[bool] = None
    min_items: Optional[int] = None
    customer_eligibility: Optional[str] = None


class CouponsResponse(SQLModel):
    data: List[CouponResponse]
    count: int


class CouponValidationResult(SQLModel):
    valid: bool
    discount_amount: Decimal
    error: Optional[str] = None
    coupon: Optional[CouponResponse] = None


class CouponValidation(SQLModel):
    coupon_code: str
    order_total: Decimal


class CouponValidationResponse(SQLModel):
    is_valid: bool
    discount_amount: Decimal
    message: Optional[str] = None
    coupon: Optional[CouponResponse] = None


class OrderCouponBase(SQLModel):
    order_id: int = Field(foreign_key="orders.order_id")
    coupon_id: int = Field(foreign_key="coupons.coupon_id")


class OrderCoupon(OrderCouponBase, table=True):
    __tablename__ = "order_coupons"

    order_coupon_id: Optional[int] = Field(default=None, primary_key=True)

    coupon: Optional["Coupon"] = Relationship(back_populates="order_coupons")
    order: Optional["Order"] = Relationship(back_populates="order_coupons")


class OrderCouponResponse(OrderCouponBase):
    order_coupon_id: int


class OrderCouponCreate(OrderCouponBase):
    pass


class FlashSaleBase(SQLModel):
    sale_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    start_time: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    )
    end_time: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    )
    discount_type: DiscountTypeEnum = Field(
        sa_column=Column(PgEnum(DiscountTypeEnum, name="discount_type_enum", create_type=True), nullable=False)
    )
    discount_value: Decimal = Field(sa_column=Column(Numeric(10, 2)), ge=0)
    is_active: bool = Field(default=True)

    @model_validator(mode='after')
    def validate_flash_sale_times(self):
        if self.end_time <= self.start_time:
            raise ValueError('end_time must be after start_time')
        return self


class FlashSale(FlashSaleBase, table=True):
    __tablename__ = "flash_sales"
    
    __table_args__ = (
        Index('idx_flash_sale_active_times', 'is_active', 'start_time', 'end_time'),
    )

    flash_sale_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    product_count: int = Field(default=0, exclude=True)

    flash_sale_products: List["FlashSaleProduct"] = Relationship(back_populates="flash_sale", cascade_delete=True)


class FlashSaleResponse(FlashSaleBase):
    flash_sale_id: int
    created_at: datetime
    product_count: int = 0


class FlashSaleCreate(FlashSaleBase):
    product_ids: Optional[List[int]] = None


class FlashSaleUpdate(SQLModel):
    sale_name: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    discount_type: Optional[DiscountTypeEnum] = None
    discount_value: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class FlashSalesResponse(SQLModel):
    data: List[FlashSaleResponse]
    count: int


class FlashSaleProductBase(SQLModel):
    flash_sale_id: int = Field(foreign_key="flash_sales.flash_sale_id")
    product_id: int = Field(foreign_key="products.product_id")
    quantity_limit: Optional[int] = Field(default=None, gt=0)
    quantity_sold: int = Field(default=0, ge=0)


class FlashSaleProduct(FlashSaleProductBase, table=True):
    __tablename__ = "flash_sale_products"

    flash_sale_product_id: Optional[int] = Field(default=None, primary_key=True)

    flash_sale: Optional["FlashSale"] = Relationship(back_populates="flash_sale_products")
    product: Optional["Product"] = Relationship(back_populates="flash_sale_products")


class FlashSaleProductResponse(FlashSaleProductBase):
    flash_sale_product_id: int


class FlashSaleProductCreate(FlashSaleProductBase):
    pass


class FlashSaleProductUpdate(SQLModel):
    quantity_limit: Optional[int] = Field(default=None, gt=0)
    quantity_sold: Optional[int] = Field(default=None, ge=0)


class FlashSaleProductsResponse(SQLModel):
    data: List[FlashSaleProductResponse]
    count: int


class FlashSaleProductAdd(SQLModel):
    product_id: int
    quantity_limit: Optional[int] = None


class FlashSaleProductDetail(SQLModel):
    flash_sale_product_id: int
    product_id: int
    quantity_limit: Optional[int]
    quantity_sold: int
    product_name: Optional[str] = None
    product_slug: Optional[str] = None
    price: Optional[Decimal] = None 
    images: Optional[List[ProductImageResponse]] = None

class FlashSaleDetailResponse(FlashSaleResponse):
    products: List[FlashSaleProductDetail] = []