from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import (
    Field,
    Relationship,
    SQLModel,
    Column,
    TIMESTAMP,
    Text,
)
from sqlalchemy import Numeric, text

from app.models.enums import ProductGenderEnum


# Product

class ProductBase(SQLModel):
    product_name: str = Field(..., max_length=255)
    slug: str | None = Field(default=None, max_length=255, index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))
    category_id: int | None = Field(default=None, foreign_key="categories.category_id")
    brand: str | None = Field(default="Adidas", max_length=100)
    collection: str | None = Field(default=None, max_length=100)
    gender: ProductGenderEnum | None = None
    base_price: Decimal = Field(sa_column=Column(Numeric(10, 2)), default=Decimal("0.00"))
    sale_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(10, 2)))
    cost_price: Decimal | None = Field(default=None, sa_column=Column(Numeric(10, 2)))
    is_featured: bool = Field(default=False)
    is_new_arrival: bool = Field(default=False)
    is_active: bool = Field(default=True)
    view_count: int = Field(default=0)
    sold_count: int = Field(default=0)
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None, sa_column=Column(Text))
    meta_keywords: str | None = Field(default=None, max_length=255)
    deleted_at: datetime | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    product_name: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    category_id: int | None = None
    brand: str | None = Field(default=None, max_length=100)
    collection: str | None = Field(default=None, max_length=100)
    gender: ProductGenderEnum | None = None
    base_price: Decimal | None = None
    sale_price: Decimal | None = None
    cost_price: Decimal | None = None
    is_featured: bool | None = None
    is_new_arrival: bool | None = None
    is_active: bool | None = None
    meta_title: str | None = Field(default=None, max_length=255)
    meta_description: str | None = Field(default=None)
    meta_keywords: str | None = Field(default=None, max_length=255)


class Product(ProductBase, table=True):
    __tablename__ = "products"

    product_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"), onupdate=text("NOW()"))
    )

    # Relationships
    category: "Category" | None = Relationship(back_populates="products")
    variants: list["ProductVariant"] = Relationship(back_populates="product", cascade_delete=True)
    images: list["ProductImage"] = Relationship(back_populates="product", cascade_delete=True)
    collection_products: list["CollectionProduct"] = Relationship(back_populates="product", cascade_delete=True)
    reviews: list["Review"] = Relationship(back_populates="product", cascade_delete=True)
    product_views: list["ProductView"] = Relationship(back_populates="product", cascade_delete=True)

    class Config:
        orm_mode = True


class ProductPublic(ProductBase):
    product_id: int
    created_at: datetime
    updated_at: datetime
    view_count: int
    sold_count: int
    is_active: bool


class ProductDetail(ProductPublic):
    variants: list["ProductVariantPublic"] = []
    images: list["ProductImagePublic"] = []


# PRODUCT VARIANT

class ProductVariantBase(SQLModel):
    sku: str = Field(..., max_length=100, index=True)
    product_id: int = Field(foreign_key="products.product_id")
    color_id: int | None = Field(default=None, foreign_key="colors.color_id")
    size_id: int | None = Field(default=None, foreign_key="sizes.size_id")
    stock_quantity: int = Field(default=0)
    low_stock_threshold: int = Field(default=5)
    weight: Decimal | None = Field(default=None, sa_column=Column(Numeric(8, 2)))
    is_available: bool = Field(default=True)


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(SQLModel):
    sku: str | None = Field(default=None, max_length=100)
    color_id: int | None = None
    size_id: int | None = None
    stock_quantity: int | None = None
    low_stock_threshold: int | None = None
    weight: Decimal | None = None
    is_available: bool | None = None


class ProductVariant(ProductVariantBase, table=True):
    __tablename__ = "product_variants"

    variant_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"), onupdate=text("NOW()"))
    )

    # Relationships
    product: Product | None = Relationship(back_populates="variants")
    color: "Color" | None = Relationship(back_populates="product_variants")
    size: "Size" | None = Relationship(back_populates="product_variants")
    images: list["ProductImage"] = Relationship(back_populates="variant", cascade_delete=True)
    inventory_logs: list["InventoryLog"] = Relationship(back_populates="variant", cascade_delete=True)
    order_items: list["OrderItem"] = Relationship(back_populates="variant")

    class Config:
        orm_mode = True


class ProductVariantPublic(ProductVariantBase):
    variant_id: int
    created_at: datetime
    updated_at: datetime
    color: "ColorPublic" | None = None
    size: "SizePublic" | None = None


# PRODUCT IMAGE

class ProductImageBase(SQLModel):
    image_url: str = Field(..., max_length=255)
    alt_text: str | None = Field(default=None, max_length=255)
    display_order: int = Field(default=0)
    is_primary: bool = Field(default=False)


class ProductImageCreate(ProductImageBase):
    product_id: int
    variant_id: int | None = None


class ProductImageUpdate(SQLModel):
    image_url: str | None = Field(default=None, max_length=255)
    alt_text: str | None = Field(default=None, max_length=255)
    display_order: int | None = None
    is_primary: bool | None = None


class ProductImage(ProductImageBase, table=True):
    __tablename__ = "product_images"

    image_id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.product_id")
    variant_id: int | None = Field(default=None, foreign_key="product_variants.variant_id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"))
    )

    # Relationships
    product: Product | None = Relationship(back_populates="images")
    variant: ProductVariant | None = Relationship(back_populates="images")

    class Config:
        orm_mode = True


class ProductImagePublic(ProductImageBase):
    image_id: int
    product_id: int
    variant_id: int | None
    created_at: datetime


# Forward references
# Để tránh circular imports, chỉ import khi type checking
if TYPE_CHECKING:
    from app.models.category import Category, CollectionProduct
    from app.models.attribute import Color, Size, ColorPublic, SizePublic
    from app.models.inventory import InventoryLog
    from app.models.order import OrderItem
    from app.models.review import Review
    from app.models.analytics import ProductView
