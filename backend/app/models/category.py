from datetime import datetime, date, timezone, timedelta
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text
from app.models.product import ProductImageResponse

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.coupon import Coupon
    

class CategoryBase(SQLModel):
    category_name: str = Field(max_length=100)
    parent_category_id: Optional[int] = Field(default=None, foreign_key="categories.category_id")
    slug: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    icon: Optional[str] = Field(default=None, max_length=100)
    image_url: Optional[str] = Field(default=None, max_length=255)
    display_order: int = Field(default=0)
    is_active: bool = Field(default=True)


class Category(CategoryBase, table=True):
    __tablename__ = "categories"
    
    category_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    
    products: List["Product"] = Relationship(back_populates="category")
    
    parent_category: Optional["Category"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={
            "remote_side": "Category.category_id",
            "foreign_keys": "[Category.parent_category_id]"
        }
    )
    children: List["Category"] = Relationship(
        back_populates="parent_category",
        sa_relationship_kwargs={
            "foreign_keys": "[Category.parent_category_id]"
        }
    )
    coupons: List["Coupon"] = Relationship(back_populates="category")


class CategoryResponse(CategoryBase):
    category_id: int
    created_at: datetime


class CategoryWithChildrenResponse(CategoryResponse):
    children: List[CategoryResponse] = []


class CategoryTreeResponse(CategoryResponse):
    children: List["CategoryTreeResponse"] = []


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    category_name: Optional[str] = Field(default=None, max_length=100)
    parent_category_id: Optional[int] = None
    slug: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=100)
    image_url: Optional[str] = Field(default=None, max_length=255)
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoriesResponse(SQLModel):
    data: List[CategoryResponse]
    count: int


class ProductCollectionBase(SQLModel):
    collection_name: str = Field(max_length=100)
    slug: Optional[str] = Field(default=None, max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    image_url: Optional[str] = Field(default=None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0)


class ProductCollection(ProductCollectionBase, table=True):
    __tablename__ = "product_collections"
    
    collection_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    
    collection_products: List["CollectionProduct"] = Relationship(
        back_populates="collection",
        cascade_delete=True
    )


class CollectionResponse(ProductCollectionBase):
    collection_id: int
    created_at: datetime


class CollectionProductDetail(SQLModel):
    category_id: int
    product_id: int
    product_name: str
    slug: Optional[str] = None
    base_price: float
    sale_price: Optional[float] = None
    images: List[ProductImageResponse] = None
    is_active: bool
    display_order: int


class CollectionWithProductsResponse(CollectionResponse):
    products: List[CollectionProductDetail] = []

class CollectionCreate(ProductCollectionBase):
    pass


class CollectionUpdate(SQLModel):
    collection_name: Optional[str] = Field(default=None, max_length=100)
    slug: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class CollectionProductBase(SQLModel):
    collection_id: int = Field(foreign_key="product_collections.collection_id")
    product_id: int = Field(foreign_key="products.product_id")
    display_order: int = Field(default=0)


class CollectionProduct(CollectionProductBase, table=True):
    __tablename__ = "collection_products"
    
    collection_product_id: Optional[int] = Field(default=None, primary_key=True)
    
    collection: Optional["ProductCollection"] = Relationship(back_populates="collection_products")
    product: Optional["Product"] = Relationship(back_populates="collection_products")


class CollectionProductAdd(SQLModel):
    product_id: int
    display_order: int = 0


class CollectionProductResponse(SQLModel):
    collection_product_id: int
    collection_id: int
    product_id: int
    display_order: int


class CollectionProductCreate(CollectionProductBase):
    pass


class CollectionProductUpdate(SQLModel):
    display_order: Optional[int] = None