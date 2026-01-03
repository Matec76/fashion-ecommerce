from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.product import Product, ProductVariant


class WishlistBase(SQLModel):
    name: str = Field(default="Yêu thích", max_length=100)
    is_default: bool = Field(default=False)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))


class Wishlist(WishlistBase, table=True):
    __tablename__ = "wishlists"

    wishlist_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    user: Optional["User"] = Relationship(back_populates="wishlists")
    items: List["WishlistItem"] = Relationship(back_populates="wishlist", cascade_delete=True)


class WishlistResponse(WishlistBase):
    wishlist_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int = 0


class WishlistDetailResponse(WishlistBase):
    wishlist_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    item_count: int
    items: List["WishlistItemResponse"] = []


class WishlistCreate(WishlistBase):
    pass


class WishlistUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=100)
    is_default: Optional[bool] = None
    description: Optional[str] = None


class WishlistsResponse(SQLModel):
    data: List[WishlistResponse]
    count: int


class WishlistItemBase(SQLModel):
    product_id: int = Field(foreign_key="products.product_id")
    variant_id: Optional[int] = Field(default=None, foreign_key="product_variants.variant_id")
    note: Optional[str] = Field(default=None, max_length=255)


class WishlistItem(WishlistItemBase, table=True):
    __tablename__ = "wishlist_items"

    wishlist_item_id: Optional[int] = Field(default=None, primary_key=True)
    wishlist_id: int = Field(foreign_key="wishlists.wishlist_id")
    added_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    wishlist: Optional["Wishlist"] = Relationship(back_populates="items")
    product: Optional["Product"] = Relationship()
    variant: Optional["ProductVariant"] = Relationship()


class WishlistItemResponse(WishlistItemBase):
    wishlist_item_id: int
    wishlist_id: int
    added_at: datetime
    product_summary: Optional[dict] = None
    variant_summary: Optional[dict] = None


class WishlistItemCreate(WishlistItemBase):
    pass


class WishlistItemUpdate(SQLModel):
    variant_id: Optional[int] = None
    note: Optional[str] = Field(default=None, max_length=255)


class WishlistItemMove(SQLModel):
    target_wishlist_id: int


class WishlistItemsResponse(SQLModel):
    data: List[WishlistItemResponse]
    count: int