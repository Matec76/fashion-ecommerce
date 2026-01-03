from typing import List, Optional, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.warehouse import (
    Warehouse,
    WarehouseCreate,
    WarehouseUpdate,
)


class CRUDWarehouse(CRUDBase[Warehouse, WarehouseCreate, WarehouseUpdate]):
    """CRUD operations cho Warehouse"""

    async def get_active(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Warehouse]:
        """
        Lấy active warehouses.
        """
        statement = (
            select(Warehouse)
            .where(Warehouse.is_active == True)
            .order_by(Warehouse.is_default.desc(), Warehouse.warehouse_name)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_default(
        self,
        *,
        db: AsyncSession
    ) -> Optional[Warehouse]:
        """
        Lấy default warehouse.
        """
        statement = select(Warehouse).where(
            Warehouse.is_default == True,
            Warehouse.is_active == True
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create_default(
        self,
        *,
        db: AsyncSession
    ) -> Warehouse:
        """
        Lấy hoặc tạo default warehouse.
        """
        warehouse = await self.get_default(db=db)
        
        if not warehouse:
            warehouse = Warehouse(
                warehouse_name="Main Warehouse",
                address="Default Address",
                city="Hanoi",
                is_active=True,
                is_default=True
            )
            db.add(warehouse)
            await db.commit()
            await db.refresh(warehouse)
        
        return warehouse

    async def set_default(
        self,
        *,
        db: AsyncSession,
        warehouse_id: int
    ) -> Warehouse:
        """
        Đặt warehouse làm default (unset các warehouse khác).
        """
        warehouse = await self.get(db=db, id=warehouse_id)
        
        if not warehouse:
            raise ValueError("Warehouse not found")
        
        if not warehouse.is_active:
            raise ValueError("Cannot set inactive warehouse as default")
        
        statement = select(Warehouse).where(
            Warehouse.is_default == True,
            Warehouse.warehouse_id != warehouse_id
        )
        result = await db.execute(statement)
        current_defaults = result.scalars().all()
        
        for wh in current_defaults:
            wh.is_default = False
            db.add(wh)
        
        warehouse.is_default = True
        db.add(warehouse)
        
        await db.commit()
        await db.refresh(warehouse)
        return warehouse

    async def get_with_stock_summary(
        self,
        *,
        db: AsyncSession,
        warehouse_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Lấy warehouse với stock summary.
        """
        from app.models.inventory import VariantStock
        
        warehouse = await self.get(db=db, id=warehouse_id)
        if not warehouse:
            return None
        
        statement = (
            select(
                func.count(func.distinct(VariantStock.variant_id)).label("total_variants"),
                func.sum(VariantStock.quantity).label("total_quantity"),
                func.sum(VariantStock.reserved).label("total_reserved")
            )
            .where(VariantStock.warehouse_id == warehouse_id)
        )
        
        result = await db.execute(statement)
        row = result.first()
        
        total_variants = row.total_variants or 0
        total_quantity = row.total_quantity or 0
        total_reserved = row.total_reserved or 0
        
        return {
            "warehouse": warehouse,
            "total_variants": total_variants,
            "total_quantity": total_quantity,
            "total_reserved": total_reserved,
            "total_available": total_quantity - total_reserved
        }

    async def get_low_stock_variants(
        self,
        *,
        db: AsyncSession,
        warehouse_id: int,
        threshold: int = 10,
        skip: int = 0,
        limit: int = 100
    ) -> List:
        """
        Lấy variants có low stock trong warehouse.
        """
        from app.models.inventory import VariantStock
        
        statement = (
            select(VariantStock)
            .options(selectinload(VariantStock.variant))
            .where(
                VariantStock.warehouse_id == warehouse_id,
                (VariantStock.quantity - VariantStock.reserved) <= threshold
            )
            .order_by((VariantStock.quantity - VariantStock.reserved))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(statement)
        return result.scalars().all()


warehouse = CRUDWarehouse(Warehouse)