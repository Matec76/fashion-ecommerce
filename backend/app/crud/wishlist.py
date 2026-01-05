from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.wishlist import (
    Wishlist,
    WishlistCreate,
    WishlistUpdate,
    WishlistItem,
    WishlistItemCreate,
    WishlistItemUpdate,
)


class CRUDWishlist(CRUDBase[Wishlist, WishlistCreate, WishlistUpdate]):

    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        load_items: bool = False
    ) -> List[Wishlist]:
        statement = select(Wishlist).where(Wishlist.user_id == user_id)
        
        if load_items:
            statement = statement.options(selectinload(Wishlist.items))
        
        statement = (
            statement
            .order_by(Wishlist.is_default.desc(), Wishlist.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_default(
        self,
        *,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Wishlist]:
        statement = (
            select(Wishlist)
            .options(selectinload(Wishlist.items))
            .where(
                Wishlist.user_id == user_id,
                Wishlist.is_default == True
            )
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create_default(
        self,
        *,
        db: AsyncSession,
        user_id: int
    ) -> Wishlist:
        wishlist = await self.get_default(db=db, user_id=user_id)
        
        if not wishlist:
            wishlist = Wishlist(
                user_id=user_id,
                name="Yêu thích",
                is_default=True,
                description="Wishlist mặc định"
            )
            db.add(wishlist)
            await db.commit()
            await db.refresh(wishlist)
        
        return wishlist

    async def set_default(
        self,
        *,
        db: AsyncSession,
        wishlist_id: int,
        user_id: int
    ) -> Wishlist:
        wishlist = await self.get(db=db, id=wishlist_id)
        
        if not wishlist or wishlist.user_id != user_id:
            raise ValueError("Wishlist not found or not owned by user")
        
        await db.execute(
            update(Wishlist)
            .where(Wishlist.user_id == user_id)
            .values(is_default=False)
        )
        
        wishlist.is_default = True
        db.add(wishlist)
        
        await db.commit()
        await db.refresh(wishlist)
        return wishlist

    async def create_for_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        obj_in: WishlistCreate,
        set_as_default: bool = False
    ) -> Wishlist:
        if set_as_default or obj_in.is_default:
            await db.execute(
                update(Wishlist)
                .where(Wishlist.user_id == user_id)
                .values(is_default=False)
            )
        
        wishlist = Wishlist(
            user_id=user_id,
            name=obj_in.name,
            is_default=set_as_default or obj_in.is_default,
            description=obj_in.description
        )
        
        db.add(wishlist)
        await db.commit()
        await db.refresh(wishlist)
        return wishlist

    async def delete_user_wishlist(
        self,
        *,
        db: AsyncSession,
        wishlist_id: int,
        user_id: int
    ) -> Optional[Wishlist]:
        statement = select(Wishlist).where(
            Wishlist.wishlist_id == wishlist_id,
            Wishlist.user_id == user_id
        )
        result = await db.execute(statement)
        wishlist = result.scalar_one_or_none()
        
        if not wishlist:
            return None
        
        await db.delete(wishlist)
        await db.commit()
        return wishlist


class CRUDWishlistItem(CRUDBase[WishlistItem, WishlistItemCreate, WishlistItemUpdate]):

    async def get_by_wishlist(
        self,
        *,
        db: AsyncSession,
        wishlist_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[WishlistItem]:
        statement = (
            select(WishlistItem)
            .options(
                selectinload(WishlistItem.product),
                selectinload(WishlistItem.variant)
            )
            .where(WishlistItem.wishlist_id == wishlist_id)
            .order_by(WishlistItem.added_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_wishlist_and_product(
        self,
        *,
        db: AsyncSession,
        wishlist_id: int,
        product_id: int,
        variant_id: Optional[int] = None
    ) -> Optional[WishlistItem]:
        statement = select(WishlistItem).where(
            WishlistItem.wishlist_id == wishlist_id,
            WishlistItem.product_id == product_id
        )
        
        if variant_id:
            statement = statement.where(WishlistItem.variant_id == variant_id)
        else:
            statement = statement.where(WishlistItem.variant_id == None)
        
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def add_item(
        self,
        *,
        db: AsyncSession,
        wishlist_id: int,
        product_id: int,
        variant_id: Optional[int] = None,
        note: Optional[str] = None
    ) -> WishlistItem:
        existing_item = await self.get_by_wishlist_and_product(
            db=db,
            wishlist_id=wishlist_id,
            product_id=product_id,
            variant_id=variant_id
        )
        
        if existing_item:
            if note:
                existing_item.note = note
                db.add(existing_item)
                await db.commit()
                await db.refresh(existing_item)
            return existing_item
        
        wishlist_item = WishlistItem(
            wishlist_id=wishlist_id,
            product_id=product_id,
            variant_id=variant_id,
            note=note
        )
        
        db.add(wishlist_item)
        await db.commit()
        await db.refresh(wishlist_item)
        return wishlist_item

    async def remove_item(
        self,
        *,
        db: AsyncSession,
        wishlist_item_id: int,
        user_id: int
    ) -> Optional[WishlistItem]:
        statement = (
            select(WishlistItem)
            .join(Wishlist)
            .where(
                WishlistItem.wishlist_item_id == wishlist_item_id,
                Wishlist.user_id == user_id
            )
        )
        result = await db.execute(statement)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        await db.delete(item)
        await db.commit()
        return item

    async def check_in_wishlist(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        product_id: int,
        variant_id: Optional[int] = None
    ) -> bool:
        statement = (
            select(WishlistItem)
            .join(Wishlist)
            .where(
                Wishlist.user_id == user_id,
                WishlistItem.product_id == product_id
            )
        )
        
        if variant_id:
            statement = statement.where(WishlistItem.variant_id == variant_id)
        
        result = await db.execute(statement)
        return result.scalar_one_or_none() is not None

    async def move_to_wishlist(
        self,
        *,
        db: AsyncSession,
        item_id: int,
        target_wishlist_id: int,
        user_id: int
    ) -> Optional[WishlistItem]:
        statement = (
            select(WishlistItem)
            .join(Wishlist)
            .where(
                WishlistItem.wishlist_item_id == item_id,
                Wishlist.user_id == user_id
            )
        )
        result = await db.execute(statement)
        item = result.scalar_one_or_none()
        
        if not item:
            return None
        
        target_statement = select(Wishlist).where(
            Wishlist.wishlist_id == target_wishlist_id,
            Wishlist.user_id == user_id
        )
        target_result = await db.execute(target_statement)
        target_wishlist = target_result.scalar_one_or_none()
        
        if not target_wishlist:
            return None
        
        existing = await self.get_by_wishlist_and_product(
            db=db,
            wishlist_id=target_wishlist_id,
            product_id=item.product_id,
            variant_id=item.variant_id
        )
        
        if existing:
            await db.delete(item)
            await db.commit()
            return existing
        
        item.wishlist_id = target_wishlist_id
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item


wishlist = CRUDWishlist(Wishlist)
wishlist_item = CRUDWishlistItem(WishlistItem)