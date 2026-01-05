from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.attribute import (
    Color,
    ColorCreate,
    ColorUpdate,
    Size,
    SizeCreate,
    SizeUpdate,
)


class CRUDColor(CRUDBase[Color, ColorCreate, ColorUpdate]):

    async def get_by_name(
        self,
        *,
        db: AsyncSession,
        name: str
    ) -> Optional[Color]:
        statement = select(Color).where(Color.color_name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_code(
        self,
        *,
        db: AsyncSession,
        code: str
    ) -> Optional[Color]:
        statement = select(Color).where(Color.color_code == code)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_active(
        self,
        *,
        db: AsyncSession
    ) -> List[Color]:
        statement = (
            select(Color)
            .where(Color.is_active == True)
            .order_by(Color.display_order, Color.color_name)
        )
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDSize(CRUDBase[Size, SizeCreate, SizeUpdate]):

    async def get_by_name(
        self,
        *,
        db: AsyncSession,
        name: str
    ) -> Optional[Size]:
        statement = select(Size).where(Size.size_name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_type(
        self,
        *,
        db: AsyncSession,
        size_type: str
    ) -> List[Size]:
        statement = (
            select(Size)
            .where(Size.size_type == size_type)
            .order_by(Size.display_order)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_active(
        self,
        *,
        db: AsyncSession,
        size_type: Optional[str] = None
    ) -> List[Size]:
        statement = select(Size).where(Size.is_active == True)
        
        if size_type:
            statement = statement.where(Size.size_type == size_type)
        
        statement = statement.order_by(Size.display_order)
        
        result = await db.execute(statement)
        return result.scalars().all()


color = CRUDColor(Color)
size = CRUDSize(Size)