from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP
from sqlalchemy import text, Numeric

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import ProductVariant


class CartBase(SQLModel):
    user_id: Optional[int] = Field(default=None, foreign_key="users.user_id")
    session_id: Optional[str] = Field(default=None, max_length=255)


class Cart(CartBase, table=True):
    __tablename__ = "carts"

    cart_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )
    expires_at: datetime | None = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))

    user: Optional["User"] = Relationship(back_populates="carts")
    items: List["CartItem"] = Relationship(back_populates="cart", cascade_delete=True)


class CartItemBase(SQLModel):
    variant_id: int = Field(foreign_key="product_variants.variant_id")
    quantity: int = Field(default=1, ge=1)


class CartItemResponse(CartItemBase):
    cart_item_id: int
    cart_id: int
    added_at: datetime
    variant: Optional[dict] = None


class CartResponse(SQLModel):
    cart_id: int
    user_id: Optional[int]
    session_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[CartItemResponse] = []
    total_items: int = 0
    subtotal: Decimal = Decimal("0")


class CartCreate(CartBase):
    pass


class CartUpdate(SQLModel):
    user_id: Optional[int] = None
    session_id: Optional[str] = None


class CartItem(CartItemBase, table=True):
    __tablename__ = "cart_items"

    cart_item_id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="carts.cart_id")
    added_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    cart: Optional["Cart"] = Relationship(back_populates="items")
    variant: Optional["ProductVariant"] = Relationship(back_populates="cart_items")


class CartItemCreate(SQLModel):
    variant_id: int
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(SQLModel):
    quantity: int = Field(ge=0)


class CartSummary(SQLModel):
    subtotal: Decimal
    discount: Decimal = Decimal("0")
    shipping_fee: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    total: Decimal
    total_items: int


class AbandonedCartBase(SQLModel):
    cart_id: int = Field(foreign_key="carts.cart_id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.user_id")
    email: Optional[str] = Field(default=None, max_length=255)
    total_items: Optional[int] = Field(default=None)
    total_value: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(18, 2)))
    email_sent_count: int = Field(default=0)
    last_email_sent: Optional[datetime] = None
    recovered: bool = Field(default=False)
    recovered_at: Optional[datetime] = None


class AbandonedCart(AbandonedCartBase, table=True):
    __tablename__ = "abandoned_carts"

    abandoned_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )


class AbandonedCartResponse(AbandonedCartBase):
    abandoned_id: int
    created_at: datetime


class AbandonedCartCreate(AbandonedCartBase):
    pass


class AbandonedCartUpdate(SQLModel):
    email_sent_count: Optional[int] = None
    last_email_sent: Optional[datetime] = None
    recovered: Optional[bool] = None
    recovered_at: Optional[datetime] = None