from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.cms import (
    BannerSlide,
    BannerSlideCreate,
    BannerSlideUpdate,
    Page,
    PageCreate,
    PageUpdate,
    Menu,
    MenuCreate,
    MenuUpdate,
    MenuItem,
    MenuItemCreate,
    MenuItemUpdate,
)


class CRUDBannerSlide(CRUDBase[BannerSlide, BannerSlideCreate, BannerSlideUpdate]):

    async def create(
        self,
        *,
        db: AsyncSession,
        obj_in: BannerSlideCreate
    ) -> BannerSlide:
        obj_in_data = jsonable_encoder(obj_in)
        
        if obj_in_data.get("start_date"):
            if obj_in.start_date:
                obj_in_data["start_date"] = obj_in.start_date.replace(tzinfo=None)

        if obj_in_data.get("end_date"):
            if obj_in.end_date:
                obj_in_data["end_date"] = obj_in.end_date.replace(tzinfo=None)

        db_obj = BannerSlide(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_active(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[BannerSlide]:
        now = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
        
        statement = (
            select(BannerSlide)
            .where(
                BannerSlide.is_active == True,
                or_(
                    BannerSlide.start_date == None,
                    BannerSlide.start_date <= now
                ),
                or_(
                    BannerSlide.end_date == None,
                    BannerSlide.end_date >= now
                )
            )
            .order_by(BannerSlide.display_order, BannerSlide.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def reorder(
        self,
        *,
        db: AsyncSession,
        banner_orders: Dict[int, int]
    ) -> List[BannerSlide]:
        banners = []
        for banner_id, display_order in banner_orders.items():
            banner = await self.get(db=db, id=banner_id)
            banner.display_order = display_order
            db.add(banner)
            banners.append(banner)
        
        await db.commit()
        
        for banner in banners:
            await db.refresh(banner)
        
        return banners


class CRUDPage(CRUDBase[Page, PageCreate, PageUpdate]):

    async def get_by_slug(
        self,
        *,
        db: AsyncSession,
        slug: str
    ) -> Optional[Page]:
        statement = select(Page).where(Page.slug == slug)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_published(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Page]:
        statement = (
            select(Page)
            .where(Page.is_published == True)
            .order_by(Page.published_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def publish(
        self,
        *,
        db: AsyncSession,
        page_id: int
    ) -> Page:
        page = await self.get(db=db, id=page_id)
        page.is_published = True
        page.published_at = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
        
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page

    async def unpublish(
        self,
        *,
        db: AsyncSession,
        page_id: int
    ) -> Page:
        page = await self.get(db=db, id=page_id)
        page.is_published = False
        
        db.add(page)
        await db.commit()
        await db.refresh(page)
        return page

    async def search(
        self,
        *,
        db: AsyncSession,
        query: str,
        published_only: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[Page]:
        statement = select(Page).where(
            or_(
                Page.title.ilike(f"%{query}%"),
                Page.content.ilike(f"%{query}%")
            )
        )
        
        if published_only:
            statement = statement.where(Page.is_published == True)
        
        statement = statement.order_by(Page.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDMenu(CRUDBase[Menu, MenuCreate, MenuUpdate]):

    async def get_by_location(
        self,
        *,
        db: AsyncSession,
        location: str
    ) -> Optional[Menu]:
        statement = (
            select(Menu)
            .options(
                selectinload(Menu.items)
                .selectinload(MenuItem.children)    
            )
            .where(
                Menu.location == location,
                Menu.is_active == True
            )
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_with_items(
        self,
        *,
        db: AsyncSession,
        menu_id: int
    ) -> Optional[Menu]:
        statement = (
            select(Menu)
            .options(
                selectinload(Menu.items).selectinload(MenuItem.children)
            )
            .where(Menu.menu_id == menu_id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_active(
        self,
        *,
        db: AsyncSession
    ) -> List[Menu]:
        statement = (
            select(Menu)
            .where(Menu.is_active == True)
            .order_by(Menu.created_at)
        )
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDMenuItem(CRUDBase[MenuItem, MenuItemCreate, MenuItemUpdate]):

    async def get_by_menu(
        self,
        *,
        db: AsyncSession,
        menu_id: int,
        parent_id: Optional[int] = None
    ) -> List[MenuItem]:
        statement = (
            select(MenuItem)
            .where(MenuItem.menu_id == menu_id)
        )
        
        if parent_id is None:
            statement = statement.where(MenuItem.parent_item_id == None)
        else:
            statement = statement.where(MenuItem.parent_item_id == parent_id)
        
        statement = statement.order_by(MenuItem.display_order, MenuItem.item_id)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_tree(
        self,
        *,
        db: AsyncSession,
        menu_id: int,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        statement = select(MenuItem).where(MenuItem.menu_id == menu_id)
        
        if active_only:
            statement = statement.where(MenuItem.is_active == True)
            
        statement = statement.order_by(MenuItem.display_order, MenuItem.item_id)
        
        result = await db.execute(statement)
        all_items = result.scalars().all()

        item_map: Dict[int, Dict[str, Any]] = {}
        
        for item in all_items:
            item_map[item.item_id] = {
                "item_id": item.item_id,
                "title": item.title,
                "url": item.url,
                "target": item.target,
                "icon": item.icon,
                "display_order": item.display_order,
                "is_active": item.is_active,
                "parent_item_id": item.parent_item_id,
                "children": []
            }

        roots = []
        for item in all_items:
            current_node = item_map[item.item_id]
            parent_id = item.parent_item_id

            if parent_id and parent_id in item_map:
                item_map[parent_id]["children"].append(current_node)
            else:
                roots.append(current_node)

        return roots

    async def reorder(
        self,
        *,
        db: AsyncSession,
        item_orders: Dict[int, int]
    ) -> List[MenuItem]:
        items = []
        for item_id, display_order in item_orders.items():
            item = await self.get(db=db, id=item_id)
            item.display_order = display_order
            db.add(item)
            items.append(item)
        
        await db.commit()
        
        for item in items:
            await db.refresh(item)
        
        return items

    async def move_item(
        self,
        *,
        db: AsyncSession,
        item_id: int,
        new_parent_id: Optional[int] = None
    ) -> MenuItem:
        item = await self.get(db=db, id=item_id)
        item.parent_item_id = new_parent_id
        
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    async def get_breadcrumbs(
        self,
        *,
        db: AsyncSession,
        item_id: int
    ) -> List[MenuItem]:
        breadcrumbs = []
        current = await self.get(db=db, id=item_id)
        
        while current:
            breadcrumbs.insert(0, current)
            if current.parent_item_id:
                current = await self.get(db=db, id=current.parent_item_id)
            else:
                break
        
        return breadcrumbs


banner_slide = CRUDBannerSlide(BannerSlide)
page = CRUDPage(Page)
menu = CRUDMenu(Menu)
menu_item = CRUDMenuItem(MenuItem)