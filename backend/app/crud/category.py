from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    ProductCollection,
    CollectionCreate,
    CollectionUpdate,
    CollectionProduct,
    CollectionProductCreate,
    CollectionProductUpdate,
)


class CRUDCategory(CRUDBase[Category, CategoryCreate, CategoryUpdate]):

    async def get_by_slug(
        self,
        *,
        db: AsyncSession,
        slug: str
    ) -> Optional[Category]:
        statement = select(Category).where(Category.slug == slug)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_with_children(
        self,
        *,
        db: AsyncSession,
        id: int
    ) -> Optional[Category]:
        statement = (
            select(Category)
            .options(selectinload(Category.children))
            .where(Category.category_id == id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_root_categories(
        self,
        *,
        db: AsyncSession,
        is_active: Optional[bool] = None
    ) -> List[Category]:
        statement = (
            select(Category)
            .where(Category.parent_category_id == None)
            .order_by(Category.display_order, Category.category_name)
        )
        
        if is_active is not None:
            statement = statement.where(Category.is_active == is_active)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_children(
        self,
        *,
        db: AsyncSession,
        parent_id: int,
        is_active: Optional[bool] = None
    ) -> List[Category]:
        statement = (
            select(Category)
            .where(Category.parent_category_id == parent_id)
            .order_by(Category.display_order, Category.category_name)
        )
        
        if is_active is not None:
            statement = statement.where(Category.is_active == is_active)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_tree(self, db: AsyncSession, is_active: bool = True) -> List[Dict[str, Any]]:
        """
        Tối ưu: Chỉ dùng 1 Query để lấy toàn bộ và dựng cây bằng Python.
        """
        stmt = select(Category).order_by(Category.display_order.asc())
        if is_active:
            stmt = stmt.where(Category.is_active == True)
        
        result = await db.execute(stmt)
        all_categories = result.scalars().all()

        category_dict = {c.category_id: {**c.model_dump(), "children": []} for c in all_categories}
        tree = []

        for c in all_categories:
            cat_node = category_dict[c.category_id]
            if c.parent_category_id is None:
                tree.append(cat_node)
            else:
                parent = category_dict.get(c.parent_category_id)
                if parent:
                    parent["children"].append(cat_node)
        
        return tree
    

    async def is_descendant(self, db: AsyncSession, parent_id: int, child_id: int) -> bool:
        """
        Kiểm tra xem child_id có phải là con/cháu của parent_id hay không.
        Dùng để chặn vòng lặp vô tận.
        """
        tree = await self.get_tree(db=db, is_active=False)
        
        def find_node(nodes, target_id):
            for n in nodes:
                if n["category_id"] == target_id:
                    return n
                res = find_node(n["children"], target_id)
                if res: return res
            return None

        parent_node = find_node(tree, parent_id)
        if not parent_node: return False
        
        return find_node(parent_node["children"], child_id) is not None
    

    async def get_breadcrumbs(
        self,
        *,
        db: AsyncSession,
        category_id: int
    ) -> List[Category]:
        breadcrumbs = []
        current = await self.get(db=db, id=category_id)
        
        while current:
            breadcrumbs.insert(0, current)
            if current.parent_category_id:
                current = await self.get(db=db, id=current.parent_category_id)
            else:
                break
        
        return breadcrumbs

    async def move_category(
        self,
        *,
        db: AsyncSession,
        category_id: int,
        new_parent_id: Optional[int] = None
    ) -> Category:
        category = await self.get(db=db, id=category_id)
        category.parent_category_id = new_parent_id
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category


class CRUDProductCollection(CRUDBase[ProductCollection, CollectionCreate, CollectionUpdate]):

    async def get_by_slug(
        self,
        *,
        db: AsyncSession,
        slug: str
    ) -> Optional[ProductCollection]:
        statement = select(ProductCollection).where(ProductCollection.slug == slug)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_active(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProductCollection]:
        statement = (
            select(ProductCollection)
            .where(ProductCollection.is_active == True)
            .order_by(ProductCollection.display_order, ProductCollection.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_with_products(
        self,
        *,
        db: AsyncSession,
        collection_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Optional[Dict[str, Any]]:
        
        from app.models.product import Product
        
        statement = (
            select(ProductCollection)
            .options(
                selectinload(ProductCollection.collection_products)
                .selectinload(CollectionProduct.product)
                .selectinload(Product.images)
            )
            .where(ProductCollection.collection_id == collection_id)
        )
        result = await db.execute(statement)
        collection = result.scalar_one_or_none()
        
        if not collection:
            return None
        
        products = [
            {   
                "category_id": cp.product.category_id,
                "product_id": cp.product.product_id,
                "product_name": cp.product.product_name,
                "slug": cp.product.slug,
                "base_price": float(cp.product.base_price),
                "sale_price": float(cp.product.sale_price) if cp.product.sale_price else None,
                "images": cp.product.images if cp.product.images else [],
                "is_active": cp.product.is_active,
                "display_order": cp.display_order,
            }
            for cp in collection.collection_products if cp.product
        ]
        
        data = collection.model_dump()
        data["products"] = products
        return data
    

    async def add_product(
        self,
        *,
        db: AsyncSession,
        collection_id: int,
        product_id: int,
        display_order: int = 0
    ) -> CollectionProduct:
        statement = select(CollectionProduct).where(
            CollectionProduct.collection_id == collection_id,
            CollectionProduct.product_id == product_id
        )
        result = await db.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        collection_product = CollectionProduct(
            collection_id=collection_id,
            product_id=product_id,
            display_order=display_order
        )
        db.add(collection_product)
        await db.commit()
        await db.refresh(collection_product)
        return collection_product

    async def remove_product(
        self,
        *,
        db: AsyncSession,
        collection_id: int,
        product_id: int
    ) -> bool:
        statement = select(CollectionProduct).where(
            CollectionProduct.collection_id == collection_id,
            CollectionProduct.product_id == product_id
        )
        result = await db.execute(statement)
        collection_product = result.scalar_one_or_none()
        
        if not collection_product:
            return False
        
        await db.delete(collection_product)
        await db.commit()
        return True


class CRUDCollectionProduct(CRUDBase[CollectionProduct, CollectionProductCreate, CollectionProductUpdate]):

    async def get_by_collection(
        self,
        *,
        db: AsyncSession,
        collection_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CollectionProduct]:
        statement = (
            select(CollectionProduct)
            .options(selectinload(CollectionProduct.product))
            .where(CollectionProduct.collection_id == collection_id)
            .order_by(CollectionProduct.display_order)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_product(
        self,
        *,
        db: AsyncSession,
        product_id: int
    ) -> List[CollectionProduct]:
        statement = (
            select(CollectionProduct)
            .options(selectinload(CollectionProduct.collection))
            .where(CollectionProduct.product_id == product_id)
        )
        result = await db.execute(statement)
        return result.scalars().all()


category = CRUDCategory(Category)
product_collection = CRUDProductCollection(ProductCollection)
collection_product = CRUDCollectionProduct(CollectionProduct)