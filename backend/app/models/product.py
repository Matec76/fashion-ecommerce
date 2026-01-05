from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import Numeric, text, CheckConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import ProductGenderEnum

if TYPE_CHECKING:
    from app.models.category import Category, CollectionProduct
    from app.models.attribute import Color, Size
    from app.models.inventory import InventoryTransaction, StockAlert, VariantStock
    from app.models.review import ProductQuestion
    from app.models.cart import CartItem
    from app.models.coupon import FlashSaleProduct
    from app.models.order import OrderItem
    from app.models.wishlist import WishlistItem
    from app.models.return_refund import ReturnItem

from app.models.attribute import ColorResponse, SizeResponse


class ProductBase(SQLModel):
    """
    Product base model.
    """
    product_name: str = Field(max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    category_id: Optional[int] = Field(default=None, foreign_key="categories.category_id")
    brand: Optional[str] = Field(default="Adidas", max_length=100)
    collection: Optional[str] = Field(default=None, max_length=100)
    gender: Optional[ProductGenderEnum] = Field(
        default=None,
        sa_column=Column(
            PgEnum(ProductGenderEnum, name="product_gender_enum", create_type=True), 
            nullable=True
        )
    )
    
    base_price: Decimal = Field(
        sa_column=Column(
            Numeric(18, 2),
            CheckConstraint('base_price >= 0'),
            nullable=False
        ),
        default=Decimal("0.00")
    )
    sale_price: Optional[Decimal] = Field(
        default=None, 
        sa_column=Column(
            Numeric(18, 2),
            CheckConstraint('sale_price IS NULL OR sale_price < base_price')
        )
    )
    cost_price: Optional[Decimal] = Field(
        default=None, 
        sa_column=Column(
            Numeric(18, 2),
            CheckConstraint('cost_price IS NULL OR cost_price >= 0')
        )
    )
    
    is_featured: bool = Field(default=False)
    is_new_arrival: bool = Field(default=False)
    is_active: bool = Field(default=True)
    view_count: int = Field(default=0)
    sold_count: int = Field(default=0)
    
    rating: Optional[Decimal] = Field(
        default=Decimal("0.00"), 
        sa_column=Column(Numeric(3, 2))
    )
    review_count: int = Field(default=0)
    
    meta_title: Optional[str] = Field(default=None, max_length=255)
    meta_description: Optional[str] = Field(default=None, sa_column=Column(Text))
    meta_keywords: Optional[str] = Field(default=None, max_length=255)
    deleted_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(TIMESTAMP(timezone=True))
    )


class Product(ProductBase, table=True):
    """Product model."""
    
    __tablename__ = "products"

    product_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(
            TIMESTAMP(timezone=True), 
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(
            TIMESTAMP(timezone=True), 
            server_default=text("CURRENT_TIMESTAMP"), 
            onupdate=text("CURRENT_TIMESTAMP")
        )
    )

    category: Optional["Category"] = Relationship(back_populates="products")
    variants: List["ProductVariant"] = Relationship(
        back_populates="product", 
        cascade_delete=True
    )
    images: List["ProductImage"] = Relationship(
        back_populates="product", 
        cascade_delete=True
    )
    collection_products: List["CollectionProduct"] = Relationship(
        back_populates="product", 
        cascade_delete=True
    )
    flash_sale_products: List["FlashSaleProduct"] = Relationship(
        back_populates="product"
    )
    product_questions: List["ProductQuestion"] = Relationship(
        back_populates="product", 
        cascade_delete=True
    )
    wishlist_items: List["WishlistItem"] = Relationship(
        back_populates="product", 
        cascade_delete=True
    )
    return_items: List["ReturnItem"] = Relationship(back_populates="product")
    attribute_values: List["ProductAttributeValue"] = Relationship(
        back_populates="product", 
        cascade_delete=True
    )


class ProductVariantBase(SQLModel):
    """Product variant base model."""
    
    product_id: int = Field(foreign_key="products.product_id")
    sku: str = Field(max_length=100, unique=True, index=True)
    color_id: Optional[int] = Field(default=None, foreign_key="colors.color_id")
    size_id: Optional[int] = Field(default=None, foreign_key="sizes.size_id")
    stock_quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5)
    weight: Optional[Decimal] = Field(
        default=None, 
        sa_column=Column(Numeric(8, 2))
    )
    is_available: bool = Field(default=True)


class ProductVariant(ProductVariantBase, table=True):
    """Product variant model."""
    
    __tablename__ = "product_variants"

    variant_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(
            TIMESTAMP(timezone=True), 
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(
            TIMESTAMP(timezone=True), 
            server_default=text("CURRENT_TIMESTAMP"), 
            onupdate=text("CURRENT_TIMESTAMP")
        )
    )

    product: Optional["Product"] = Relationship(back_populates="variants")
    color: Optional["Color"] = Relationship(back_populates="product_variants")
    size: Optional["Size"] = Relationship(back_populates="product_variants")
    images: List["ProductImage"] = Relationship(
        back_populates="variant", 
        cascade_delete=True
    )
    inventory_transactions: List["InventoryTransaction"] = Relationship(
        back_populates="variant", 
        cascade_delete=True
    )
    stock_alerts: List["StockAlert"] = Relationship(
        back_populates="variant", 
        cascade_delete=True
    )
    warehouse_stocks: List["VariantStock"] = Relationship(
        back_populates="variant", 
        cascade_delete=True
    )
    order_items: List["OrderItem"] = Relationship(back_populates="variant")
    cart_items: List["CartItem"] = Relationship(back_populates="variant")
    wishlist_items: List["WishlistItem"] = Relationship(back_populates="variant")
    return_items: List["ReturnItem"] = Relationship(back_populates="variant")


class ProductVariantResponse(ProductVariantBase):
    """Product variant response schema."""
    
    variant_id: int
    created_at: datetime
    updated_at: datetime
    color: Optional[ColorResponse] = None
    size: Optional[SizeResponse] = None


class ProductVariantCreate(ProductVariantBase):
    """Product variant creation schema."""
    pass


class ProductVariantUpdate(SQLModel):
    """Product variant update schema."""
    
    sku: Optional[str] = Field(default=None, max_length=100)
    color_id: Optional[int] = None
    size_id: Optional[int] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    low_stock_threshold: Optional[int] = None
    weight: Optional[Decimal] = None
    is_available: Optional[bool] = None


class ProductVariantsResponse(SQLModel):
    """List of product variants response."""
    
    data: List[ProductVariantResponse]
    count: int


class ProductImageBase(SQLModel):
    """Product image base model."""
    
    product_id: int = Field(foreign_key="products.product_id")
    variant_id: Optional[int] = Field(
        default=None, 
        foreign_key="product_variants.variant_id"
    )
    image_url: str = Field(max_length=255)
    alt_text: Optional[str] = Field(default=None, max_length=255)
    display_order: int = Field(default=0)
    is_primary: bool = Field(default=False)


class ProductImage(ProductImageBase, table=True):
    """Product image model."""
    
    __tablename__ = "product_images"

    image_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(
            TIMESTAMP(timezone=True), 
            server_default=text("CURRENT_TIMESTAMP")
        )
    )

    product: Optional["Product"] = Relationship(back_populates="images")
    variant: Optional["ProductVariant"] = Relationship(back_populates="images")


class ProductImageResponse(ProductImageBase):
    """Product image response schema."""
    
    image_id: int
    created_at: datetime


class ProductImageCreate(ProductImageBase):
    """Product image creation schema."""
    pass


class ProductImageUpdate(SQLModel):
    """Product image update schema."""
    
    image_url: Optional[str] = Field(default=None, max_length=255)
    alt_text: Optional[str] = Field(default=None, max_length=255)
    display_order: Optional[int] = None
    is_primary: Optional[bool] = None


class ProductImagesResponse(SQLModel):
    """List of product images response."""
    
    data: List[ProductImageResponse]
    count: int


class ProductResponse(ProductBase):
    """Product response schema."""
    
    product_id: int
    created_at: datetime
    updated_at: datetime


class ProductDetailResponse(ProductResponse):
    """Product detail response with relationships."""
    
    variants: List[ProductVariantResponse] = []
    images: List[ProductImageResponse] = []


class ProductCreate(SQLModel):
    """
    Product creation schema.
    """
    product_name: str = Field(max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = Field(default="Adidas", max_length=100)
    collection: Optional[str] = Field(default=None, max_length=100)
    gender: Optional[ProductGenderEnum] = None
    base_price: Decimal = Field(ge=0)
    sale_price: Optional[Decimal] = Field(default=None, ge=0)
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    is_featured: Optional[bool] = False
    is_new_arrival: Optional[bool] = False
    is_active: Optional[bool] = True
    meta_title: Optional[str] = Field(default=None, max_length=255)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = Field(default=None, max_length=255)


class ProductUpdate(SQLModel):
    """Product update schema."""
    
    product_name: Optional[str] = Field(default=None, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = Field(default=None, max_length=100)
    collection: Optional[str] = Field(default=None, max_length=100)
    gender: Optional[ProductGenderEnum] = None
    base_price: Optional[Decimal] = Field(default=None, ge=0)
    sale_price: Optional[Decimal] = Field(default=None, ge=0)
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    is_featured: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    is_active: Optional[bool] = None
    meta_title: Optional[str] = Field(default=None, max_length=255)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = Field(default=None, max_length=255)


class ProductsResponse(SQLModel):
    """List of products response."""
    
    data: List[ProductResponse]
    count: int



class ProductAttributeBase(SQLModel):
    """Product attribute base model."""
    
    attribute_name: str = Field(max_length=100, unique=True)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class ProductAttribute(ProductAttributeBase, table=True):
    """Product attribute model."""
    
    __tablename__ = "product_attributes"

    attribute_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(
            TIMESTAMP(timezone=True), 
            server_default=text("CURRENT_TIMESTAMP")
        )
    )
    
    values: List["ProductAttributeValue"] = Relationship(
        back_populates="attribute", 
        cascade_delete=True
    )


class ProductAttributeValueBase(SQLModel):
    """Product attribute value base model."""
    
    product_id: int = Field(foreign_key="products.product_id")
    attribute_id: int = Field(foreign_key="product_attributes.attribute_id")
    attribute_value: str = Field(max_length=255)


class ProductAttributeValue(ProductAttributeValueBase, table=True):
    """Product attribute value model."""
    
    __tablename__ = "product_attribute_values"
    
    value_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(
            TIMESTAMP(timezone=True), 
            server_default=text("CURRENT_TIMESTAMP")
        )
    )

    product: Optional["Product"] = Relationship(back_populates="attribute_values")
    attribute: Optional["ProductAttribute"] = Relationship(back_populates="values")