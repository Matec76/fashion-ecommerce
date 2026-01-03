from typing import List, Optional, Dict
from decimal import Decimal

from sqlalchemy import select, or_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta

from app.crud.base import CRUDBase
from app.models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
    ProductVariant,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductImage,
    ProductImageCreate,
    ProductImageUpdate,
)
from app.models.enums import ProductGenderEnum
from app.crud.system import system_setting


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    """Product CRUD operations."""

    async def get_by_slug(
        self,
        *,
        db: AsyncSession,
        slug: str
    ) -> Optional[Product]:
        """Get product by slug."""
        statement = select(Product).where(Product.slug == slug)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_with_details(
        self,
        *,
        db: AsyncSession,
        id: int
    ) -> Optional[Product]:
        """Get product with all related data."""
        statement = (
            select(Product)
            .options(
                selectinload(Product.variants).selectinload(ProductVariant.color),
                selectinload(Product.variants).selectinload(ProductVariant.size),
                selectinload(Product.images),
                selectinload(Product.category)
            )
            .where(Product.product_id == id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    def _apply_sorting(
        self,
        statement: select,
        sort_by: Optional[str] = None
    ) -> select:
        """
        Apply sorting to query.
        
        Args:
            statement: SQLAlchemy select statement
            sort_by: Sort field
        
        Returns:
            Statement with sorting applied
        """
        if not sort_by:
            return statement.order_by(Product.created_at.desc())
        
        sort_mapping = {
            "created_at": Product.created_at.desc(),
            "created_at_asc": Product.created_at.asc(),
            "price_asc": func.coalesce(Product.sale_price, Product.base_price).asc(),
            "price_desc": func.coalesce(Product.sale_price, Product.base_price).desc(),
            "name": Product.product_name.asc(),
            "name_desc": Product.product_name.desc(),
            "rating": Product.rating.desc().nullslast(),
            "popularity": Product.view_count.desc(),
            "best_selling": Product.sold_count.desc(),
        }
        
        sort_column = sort_mapping.get(sort_by)
        if sort_column is not None:
            return statement.order_by(sort_column)
        
        return statement.order_by(Product.created_at.desc())

    async def get_active(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        gender: Optional[ProductGenderEnum] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        brand: Optional[str] = None,
        is_new_arrival: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        sort_by: Optional[str] = None,
    ) -> List[Product]:
        """Get active products with filters."""
        statement = select(Product).where(Product.is_active == True)
        
        if category_id:
            statement = statement.where(Product.category_id == category_id)
        
        if gender:
            statement = statement.where(Product.gender == gender)

        if brand:
            statement = statement.where(Product.brand == brand)

        if is_new_arrival is not None:
            statement = statement.where(Product.is_new_arrival == is_new_arrival)

        if is_featured is not None:
            statement = statement.where(Product.is_featured == is_featured)
        
        if min_price is not None or max_price is not None:
            effective_price = func.coalesce(Product.sale_price, Product.base_price)
            if min_price is not None:
                statement = statement.where(effective_price >= min_price)
            if max_price is not None:
                statement = statement.where(effective_price <= max_price)
        
        statement = self._apply_sorting(statement, sort_by)
        
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_featured(
        self,
        *,
        db: AsyncSession,
        category_id: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Product]:
        if limit is None:
            limit_str = await system_setting.get_value(db=db, key="featured_products_limit", default=12)
            limit = int(limit_str)
        
        statement = select(Product).where(
            Product.is_active == True,
            Product.is_featured == True
        )
        
        if category_id:
            statement = statement.where(Product.category_id == category_id)
            
        statement = statement.order_by(Product.view_count.desc(), Product.created_at.desc()).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())


    async def get_new_arrivals(
        self,
        *,
        db: AsyncSession,
        category_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Product]:
        statement = select(Product).where(
            Product.is_active == True,
            Product.is_new_arrival == True
        )
        if category_id:
            statement = statement.where(Product.category_id == category_id)
            
        statement = statement.order_by(Product.created_at.desc()).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())


    async def get_best_sellers(
        self,
        *,
        db: AsyncSession,
        category_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Product]:
        statement = select(Product).where(Product.is_active == True)
        
        if category_id:
            statement = statement.where(Product.category_id == category_id)
            
        statement = statement.order_by(Product.sold_count.desc(), Product.rating.desc().nullslast()).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())
    

    async def search(
        self,
        *,
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        brand: Optional[str] = None,
        gender: Optional[ProductGenderEnum] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        is_featured: Optional[bool] = None,
        sort_by: Optional[str] = None,
    ) -> List[Product]:
        """Search products with filters."""
        min_length_str = await system_setting.get_value(
            db=db, 
            key="search_min_query_length", 
            default=2
        )
        min_length = int(min_length_str)
        if len(query) < min_length:
            return []
        
        search_term = f"%{query.lower()}%"
        
        statement = select(Product).where(
            Product.is_active == True,
            or_(
                func.lower(Product.product_name).like(search_term),
                func.lower(Product.description).like(search_term),
                func.lower(Product.brand).like(search_term)
            )
        )
        
        if category_id:
            statement = statement.where(Product.category_id == category_id)
        
        if brand:
            statement = statement.where(Product.brand == brand)
        
        if gender:
            statement = statement.where(Product.gender == gender)
        
        if is_featured is not None:
            statement = statement.where(Product.is_featured == is_featured)
        
        if min_price is not None or max_price is not None:
            effective_price = func.coalesce(Product.sale_price, Product.base_price)
            if min_price is not None:
                statement = statement.where(effective_price >= min_price)
            if max_price is not None:
                statement = statement.where(effective_price <= max_price)
        
        if not sort_by:
            statement = statement.order_by(Product.view_count.desc())
        else:
            statement = self._apply_sorting(statement, sort_by)
        
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def increment_view_count(
        self,
        *,
        db: AsyncSession,
        product_id: int
    ) -> Optional[Product]:
        """
        ATOMIC: Increment product view count
        """
        stmt = (
            update(Product)
            .where(Product.product_id == product_id)
            .values(view_count=Product.view_count + 1)
            .returning(Product)
        )
        
        result = await db.execute(stmt)
        product = result.scalar_one_or_none()
        
        if product:
            await db.commit()
        
        return product

    async def update_rating(
        self,
        *,
        db: AsyncSession,
        product_id: int
    ) -> Optional[Product]:
        """Update product rating based on reviews."""
        from app.models.review import Review
        
        statement = select(
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.review_id).label('review_count')
        ).where(
            Review.product_id == product_id,
            Review.is_approved == True
        )
        result = await db.execute(statement)
        row = result.first()
        
        product = await self.get(db=db, id=product_id)
        if product:
            product.rating = Decimal(str(row.avg_rating)) if row.avg_rating else None
            product.review_count = row.review_count if row.review_count else 0
            
            db.add(product)
            await db.commit()
            await db.refresh(product)
        return product

    async def get_related_products(
        self,
        *,
        db: AsyncSession,
        product_id: int,
        limit: Optional[int] = None
    ) -> List[Product]:
        """Get related products based on category."""
        if limit is None:
            limit_str = await system_setting.get_value(
                db=db, 
                key="related_products_limit", 
                default=8
            )
            limit = int(limit_str)
        
        product = await self.get(db=db, id=product_id)
        if not product:
            return []
        
        statement = (
            select(Product)
            .where(
                Product.is_active == True,
                Product.category_id == product.category_id,
                Product.product_id != product_id
            )
            .order_by(Product.view_count.desc())
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_category(
        self,
        *,
        db: AsyncSession,
        category_id: int,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None
    ) -> List[Product]:
        """Get products by category."""
        statement = select(Product).where(
            Product.is_active == True,
            Product.category_id == category_id
        )
        
        statement = self._apply_sorting(statement, sort_by)
        
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_price_range(
        self,
        *,
        db: AsyncSession,
        category_id: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """Get min and max prices for filtering."""
        effective_price = func.coalesce(Product.sale_price, Product.base_price)
        
        statement = select(
            func.min(effective_price).label('min_price'),
            func.max(effective_price).label('max_price')
        ).where(Product.is_active == True)
        
        if category_id:
            statement = statement.where(Product.category_id == category_id)
        
        result = await db.execute(statement)
        row = result.first()
        
        return {
            "min_price": row.min_price or Decimal("0"),
            "max_price": row.max_price or Decimal("0")
        }
    
    async def count_low_stock(
        self,
        *,
        db: AsyncSession
    ) -> int:
        """Count total variants with low stock."""
        threshold_str = await system_setting.get_value(
            db=db, 
            key="low_stock_threshold", 
            default=5
        )
        threshold = int(threshold_str)
        
        statement = select(func.count(ProductVariant.variant_id)).where(
            ProductVariant.stock_quantity <= threshold
        )
        result = await db.execute(statement)
        return result.scalar() or 0

    async def update_sold_count(
        self,
        *,
        db: AsyncSession,
        product_id: int,
        quantity: int
    ):
        """
        Cập nhật số lượng đã bán (Atomic Update).
        Dùng func.greatest(0, ...) để đảm bảo không bị âm.
        """
        statement = (
            update(Product)
            .where(Product.product_id == product_id)
            .values(
                sold_count=func.greatest(0, Product.sold_count + quantity)
            )
        )
        await db.execute(statement)


class CRUDProductVariant(CRUDBase[ProductVariant, ProductVariantCreate, ProductVariantUpdate]):
    """Product variant CRUD operations."""

    async def get_by_sku(
        self,
        *,
        db: AsyncSession,
        sku: str
    ) -> Optional[ProductVariant]:
        """Get variant by SKU."""
        statement = select(ProductVariant).where(ProductVariant.sku == sku)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_with_details(
        self,
        *,
        db: AsyncSession,
        id: int
    ) -> Optional[ProductVariant]:
        """Get variant with product, color, and size details."""
        statement = (
            select(ProductVariant)
            .options(
                selectinload(ProductVariant.product),
                selectinload(ProductVariant.color),
                selectinload(ProductVariant.size)
            )
            .where(ProductVariant.variant_id == id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_product(
        self,
        *,
        db: AsyncSession,
        product_id: int
    ) -> List[ProductVariant]:
        """Get all variants for a product."""
        statement = (
            select(ProductVariant)
            .options(
                selectinload(ProductVariant.color),
                selectinload(ProductVariant.size)
            )
            .where(ProductVariant.product_id == product_id)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_product_and_attributes(
        self,
        *,
        db: AsyncSession,
        product_id: int,
        color_id: Optional[int] = None,
        size_id: Optional[int] = None
    ) -> Optional[ProductVariant]:
        """Get variant by product and attributes."""
        statement = select(ProductVariant).where(
            ProductVariant.product_id == product_id
        )
        
        if color_id:
            statement = statement.where(ProductVariant.color_id == color_id)
        else:
            statement = statement.where(ProductVariant.color_id.is_(None))
        
        if size_id:
            statement = statement.where(ProductVariant.size_id == size_id)
        else:
            statement = statement.where(ProductVariant.size_id.is_(None))
        
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def update_stock(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        quantity_change: int,
        flush: bool = False
    ) -> Optional[ProductVariant]:
        """
        Update variant stock quantity (deprecated - use update_stock_with_lock instead).
        """
        variant = await self.get(db=db, id=variant_id)
        if variant:
            variant.stock_quantity = max(0, (variant.stock_quantity or 0) + quantity_change)
            variant.is_available = variant.stock_quantity > 0
            
            db.add(variant)
            
            if flush:
                await db.flush()
            else:
                await db.commit()
                await db.refresh(variant)
        
        return variant

    async def update_stock_with_lock(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        quantity: int,
        increment: bool = False
    ) -> bool:
        """
        Cập nhật tồn kho an toàn (Atomic Update)
        
        Trả về True nếu thành công, False nếu thất bại (hết hàng/không tìm thấy).
        
        Args:
            db: Database session
            variant_id: ID của variant cần update
            quantity: Số lượng cần thay đổi
            increment: True = tăng stock (hoàn trả), False = giảm stock (bán hàng)
        
        Returns:
            bool: True nếu update thành công, False nếu không đủ stock hoặc variant không tồn tại
        """
        if increment:
            stmt = (
                update(ProductVariant)
                .where(ProductVariant.variant_id == variant_id)
                .values(
                    stock_quantity=ProductVariant.stock_quantity + quantity,
                    updated_at=datetime.now(timezone(timedelta(hours=7))),
                    is_available=True
                )
            )
        else:
            stmt = (
                update(ProductVariant)
                .where(
                    ProductVariant.variant_id == variant_id,
                    ProductVariant.stock_quantity >= quantity
                )
                .values(
                    stock_quantity=ProductVariant.stock_quantity - quantity,
                    updated_at=datetime.now(timezone(timedelta(hours=7))),
                    is_available=(ProductVariant.stock_quantity - quantity) > 0
                )
            )
        
        result = await db.execute(stmt)
        
        return result.rowcount > 0

    async def check_stock_availability(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        quantity: int
    ) -> bool:
        """
        Check if variant has enough stock.
        
        Note: Nên tránh dùng hàm này trước khi update để tránh race condition.
        Thay vào đó dùng update_stock_with_lock() trực tiếp.
        """
        variant = await self.get(db=db, id=variant_id)
        if not variant:
            return False
        return (variant.stock_quantity or 0) >= quantity and variant.is_available

    async def get_low_stock(
        self,
        *,
        db: AsyncSession,
        threshold: Optional[int] = None,
        limit: int = 100
    ) -> List[ProductVariant]:
        """Get variants with low stock."""
        if threshold is None:
            threshold_str = await system_setting.get_value(
                db=db, 
                key="low_stock_threshold", 
                default=5
            )
            threshold = int(threshold_str)
        
        statement = (
            select(ProductVariant)
            .options(selectinload(ProductVariant.product))
            .where(ProductVariant.stock_quantity <= threshold)
            .order_by(ProductVariant.stock_quantity)
            .limit(limit)
        )
        
        result = await db.execute(statement)
        return list(result.scalars().all())


class CRUDProductImage(CRUDBase[ProductImage, ProductImageCreate, ProductImageUpdate]):
    """Product image CRUD operations."""

    async def get_by_product(
        self,
        *,
        db: AsyncSession,
        product_id: int
    ) -> List[ProductImage]:
        """Get all images for a product."""
        statement = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.display_order, ProductImage.created_at)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_primary_image(
        self,
        *,
        db: AsyncSession,
        product_id: int
    ) -> Optional[ProductImage]:
        """Get primary image for a product."""
        statement = select(ProductImage).where(
            ProductImage.product_id == product_id,
            ProductImage.is_primary == True
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def set_primary(
        self,
        *,
        db: AsyncSession,
        image_id: int,
        product_id: int
    ) -> Optional[ProductImage]:
        """
        Set image as primary (unset others).
        
        Sử dụng 2 UPDATE statements trong 1 transaction
        """
        await db.execute(
            update(ProductImage)
            .where(
                ProductImage.product_id == product_id,
                ProductImage.is_primary == True
            )
            .values(is_primary=False)
        )
        
        stmt = (
            update(ProductImage)
            .where(ProductImage.image_id == image_id)
            .values(is_primary=True)
            .returning(ProductImage)
        )
        
        result = await db.execute(stmt)
        image = result.scalar_one_or_none()
        
        if image:
            await db.commit()
        
        return image


product = CRUDProduct(Product)
product_variant = CRUDProductVariant(ProductVariant)
product_image = CRUDProductImage(ProductImage)