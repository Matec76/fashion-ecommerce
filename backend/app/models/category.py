from datetime import datetime, date
from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text


# Category

class CategoryBase(SQLModel):
    category_name: str = Field(max_length=100)
    parent_category_id: int | None = Field(default=None, foreign_key="categories.category_id")
    slug: str | None = Field(default=None, max_length=100, unique=True, index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))
    image_url: str | None = Field(default=None, max_length=255)
    display_order: int = Field(default=0)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(SQLModel):
    category_name: str | None = Field(default=None, max_length=100)
    parent_category_id: int | None = None
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=255)
    display_order: int | None = None
    is_active: bool | None = None


class Category(CategoryBase, table=True):
    __tablename__ = "categories"
    
    category_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"))
    )
    
    # Relationships
    products: list["Product"] = Relationship(back_populates="category")
    
    # Self-referencing relationship cho category tree
    parent_category: "Category" | None = Relationship(
        back_populates="sub_categories",
        sa_relationship_kwargs={
            "remote_side": "Category.category_id",
            "foreign_keys": "[Category.parent_category_id]"
        }
    )
    sub_categories: list["Category"] = Relationship(
        back_populates="parent_category",
        sa_relationship_kwargs={
            "foreign_keys": "[Category.parent_category_id]"
        }
    )


class CategoryPublic(CategoryBase):
    category_id: int
    created_at: datetime


class CategoryPublicWithChildren(CategoryPublic):
    sub_categories: list[CategoryPublic] = []


class CategoriesPublic(SQLModel):
    data: list[CategoryPublic]
    count: int


class CategoryTree(CategoryPublic):
    sub_categories: list["CategoryTree"] = []


# Product Collection

class ProductCollectionBase(SQLModel):
    collection_name: str = Field(max_length=100)
    slug: str | None = Field(default=None, max_length=100, unique=True, index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))
    image_url: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True
    display_order: int = Field(default=0)


class ProductCollectionCreate(ProductCollectionBase):
    pass


class ProductCollectionUpdate(SQLModel):
    collection_name: str | None = Field(default=None, max_length=100)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = None
    image_url: str | None = Field(default=None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    display_order: int | None = None


class ProductCollection(ProductCollectionBase, table=True):
    __tablename__ = "product_collections"
    
    collection_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"))
    )
    
    # Relationships
    collection_products: list["CollectionProduct"] = Relationship(
        back_populates="collection",
        cascade_delete=True
    )


class ProductCollectionPublic(ProductCollectionBase):
    collection_id: int
    created_at: datetime


class ProductCollectionsPublic(SQLModel):
    data: list[ProductCollectionPublic]
    count: int


# Collection-Product Junction Table

class CollectionProductBase(SQLModel):
    collection_id: int = Field(foreign_key="product_collections.collection_id")
    product_id: int = Field(foreign_key="products.product_id")
    display_order: int = Field(default=0)


class CollectionProductCreate(CollectionProductBase):
    pass


class CollectionProductUpdate(SQLModel):
    display_order: int | None = None


class CollectionProduct(CollectionProductBase, table=True):
    __tablename__ = "collection_products"
    
    collection_product_id: int | None = Field(default=None, primary_key=True)
    
    # Relationships
    collection: ProductCollection = Relationship(back_populates="collection_products")
    product: "Product" = Relationship(back_populates="collection_products")


class CollectionProductPublic(SQLModel):
    collection_product_id: int
    collection_id: int
    product_id: int
    display_order: int


# Forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.product import Product