from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.inventory import (
    InventoryTransaction,
    InventoryTransactionCreate,
    VariantStock,
    VariantStockCreate,
    VariantStockUpdate,
    StockAlert,
    StockAlertCreate,
    StockAlertUpdate,
)
from app.models.product import ProductVariant
from app.models.enums import InventoryChangeEnum, StockAlertTypeEnum
from app.crud.system import system_setting


class CRUDInventoryTransaction(CRUDBase[InventoryTransaction, InventoryTransactionCreate, Dict[str, Any]]):
    """CRUD operations cho InventoryTransaction"""

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100, 
        variant_id: int | None = None,
        warehouse_id: int | None = None
    ) -> List[InventoryTransaction]:
        """
        Lấy danh sách transaction có kèm thông tin Variant và Product.
        """
        statement = select(InventoryTransaction).options(
            selectinload(InventoryTransaction.variant).selectinload(ProductVariant.product),
            selectinload(InventoryTransaction.user),
            selectinload(InventoryTransaction.warehouse)
        )
        
        if variant_id:
            statement = statement.where(InventoryTransaction.variant_id == variant_id)
        if warehouse_id:
            statement = statement.where(InventoryTransaction.warehouse_id == warehouse_id)
            
        statement = statement.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()


    async def create_transaction(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        warehouse_id: int,
        transaction_type: InventoryChangeEnum,
        quantity: int,
        performed_by: Optional[int] = None,
        reference: Optional[str] = None,
        note: Optional[str] = None
    ) -> InventoryTransaction:
        """
        Tạo inventory transaction, cập nhật stock kho và đồng bộ tổng về ProductVariant.
        """
        stock = await variant_stock.get_or_create(
            db=db,
            variant_id=variant_id,
            warehouse_id=warehouse_id
        )
        
        if transaction_type in [
            InventoryChangeEnum.IMPORT, 
            InventoryChangeEnum.RETURN, 
            InventoryChangeEnum.TRANSFER_IN
        ]:
            change_amount = quantity
            
        elif transaction_type in [
            InventoryChangeEnum.SALE,
            InventoryChangeEnum.DAMAGED,
            InventoryChangeEnum.TRANSFER_OUT
        ]:
            change_amount = -quantity
            
        elif transaction_type == InventoryChangeEnum.ADJUSTMENT:
            change_amount = quantity 
        else:
            change_amount = quantity

        current_qty = stock.quantity if stock.quantity is not None else 0
        balance_after = current_qty + change_amount
        
        transaction = InventoryTransaction(
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            transaction_type=transaction_type,
            quantity=quantity,
            balance_after=balance_after,
            performed_by=performed_by,
            reference=reference,
            note=note
        )
        db.add(transaction)
        
        stock.quantity = balance_after
        stock.updated_at = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
        await db.merge(stock)

        await db.flush()
        
        stmt_total = select(func.sum(VariantStock.quantity)).where(
            VariantStock.variant_id == variant_id
        )
        result_total = await db.execute(stmt_total)
        total_quantity = result_total.scalar() or 0
        
        stmt_update_variant = (
            update(ProductVariant)
            .where(ProductVariant.variant_id == variant_id)
            .values(stock_quantity=total_quantity) 
        )
        await db.execute(stmt_update_variant)

        await db.commit()
        await db.refresh(transaction)
        
        try:
            await self._check_stock_alerts(db=db, variant_id=variant_id, warehouse_id=warehouse_id)
        except Exception:
            pass
        
        return transaction

    async def get_by_variant(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        warehouse_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """
        Lấy transactions của variant.
        """
        statement = (
            select(InventoryTransaction)
            .options(
                selectinload(InventoryTransaction.warehouse),
                selectinload(InventoryTransaction.user)
            )
            .where(InventoryTransaction.variant_id == variant_id)
        )
        
        if warehouse_id:
            statement = statement.where(InventoryTransaction.warehouse_id == warehouse_id)
        
        statement = statement.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_warehouse(
        self,
        *,
        db: AsyncSession,
        warehouse_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryTransaction]:
        """
        Lấy transactions của warehouse.
        """
        statement = (
            select(InventoryTransaction)
            .options(
                selectinload(InventoryTransaction.variant),
                selectinload(InventoryTransaction.user)
            )
            .where(InventoryTransaction.warehouse_id == warehouse_id)
            .order_by(InventoryTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def _check_stock_alerts(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        warehouse_id: int
    ):
        """Check and create stock alerts if needed."""
        stock = await variant_stock.get_by_variant_warehouse(
            db=db,
            variant_id=variant_id,
            warehouse_id=warehouse_id
        )
        
        if not stock:
            return
        
        low_stock_threshold_str = await system_setting.get_value(
            db=db, 
            key="low_stock_threshold", 
            default=5
        )
        low_stock_threshold = int(low_stock_threshold_str)
        
        if stock.available <= low_stock_threshold and stock.available > 0:
            await stock_alert.create_if_not_exists(
                db=db,
                variant_id=variant_id,
                alert_type=StockAlertTypeEnum.LOW_STOCK,
                threshold=low_stock_threshold,
                current_stock=stock.available
            )
        
        if stock.available == 0:
            await stock_alert.create_if_not_exists(
                db=db,
                variant_id=variant_id,
                alert_type=StockAlertTypeEnum.OUT_OF_STOCK,
                threshold=0,
                current_stock=0
            )


class CRUDVariantStock(CRUDBase[VariantStock, VariantStockCreate, VariantStockUpdate]):
    """CRUD operations cho VariantStock"""

    async def get_or_create(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        warehouse_id: int
    ) -> VariantStock:
        """
        Lấy hoặc tạo stock record.
        """
        stock = await self.get_by_variant_warehouse(
            db=db,
            variant_id=variant_id,
            warehouse_id=warehouse_id
        )
        
        if not stock:
            stock = VariantStock(
                variant_id=variant_id,
                warehouse_id=warehouse_id,
                quantity=0,
                reserved=0
            )
            db.add(stock)
            await db.commit()
            await db.refresh(stock)
        
        return stock

    async def get_by_variant_warehouse(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        warehouse_id: int
    ) -> Optional[VariantStock]:
        """
        Lấy stock theo variant và warehouse.
        """
        statement = select(VariantStock).where(
            VariantStock.variant_id == variant_id,
            VariantStock.warehouse_id == warehouse_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_variant(
        self,
        *,
        db: AsyncSession,
        variant_id: int
    ) -> List[VariantStock]:
        """
        Lấy stock của variant ở tất cả warehouses.
        """
        statement = (
            select(VariantStock)
            .options(selectinload(VariantStock.warehouse))
            .where(VariantStock.variant_id == variant_id)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_warehouse(
        self,
        *,
        db: AsyncSession,
        warehouse_id: int,
        skip: int = 0,
        limit: int = 1000
    ) -> List[VariantStock]:
        """
        Lấy tất cả stock trong warehouse.
        """
        statement = (
            select(VariantStock)
            .options(selectinload(VariantStock.variant))
            .where(VariantStock.warehouse_id == warehouse_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def reserve_stock(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        warehouse_id: int,
        quantity: int
    ) -> VariantStock:
        """
        Reserve stock cho order.
        """
        stock = await self.get_or_create(
            db=db,
            variant_id=variant_id,
            warehouse_id=warehouse_id
        )
        
        if stock.available < quantity:
            raise ValueError(f"Not enough stock. Available: {stock.available}, Required: {quantity}")
        
        stock.reserved += quantity
        db.add(stock)
        await db.commit()
        await db.refresh(stock)
        
        return stock

    async def release_stock(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        warehouse_id: int,
        quantity: int
    ) -> VariantStock:
        """
        Release reserved stock (e.g., when order cancelled).
        """
        stock = await self.get_or_create(
            db=db,
            variant_id=variant_id,
            warehouse_id=warehouse_id
        )
        
        stock.reserved = max(0, stock.reserved - quantity)
        db.add(stock)
        await db.commit()
        await db.refresh(stock)
        
        return stock

    async def get_total_stock(
        self,
        *,
        db: AsyncSession,
        variant_id: int
    ) -> Dict[str, int]:
        """
        Lấy tổng stock của variant qua tất cả warehouses.
        """
        statement = (
            select(
                func.sum(VariantStock.quantity).label("total_quantity"),
                func.sum(VariantStock.reserved).label("total_reserved")
            )
            .where(VariantStock.variant_id == variant_id)
        )
        
        result = await db.execute(statement)
        row = result.first()
        
        total_quantity = row.total_quantity or 0
        total_reserved = row.total_reserved or 0
        
        return {
            "total_quantity": total_quantity,
            "total_reserved": total_reserved,
            "total_available": total_quantity - total_reserved
        }


class CRUDStockAlert(CRUDBase[StockAlert, StockAlertCreate, StockAlertUpdate]):
    """CRUD operations cho StockAlert"""

    async def create_if_not_exists(
        self,
        *,
        db: AsyncSession,
        variant_id: int,
        alert_type: StockAlertTypeEnum,
        threshold: int,
        current_stock: int
    ) -> Optional[StockAlert]:
        """
        Tạo alert nếu chưa có unresolved alert cùng type.
        """
        statement = select(StockAlert).where(
            StockAlert.variant_id == variant_id,
            StockAlert.alert_type == alert_type,
            StockAlert.is_resolved == False
        )
        result = await db.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            return None
        
        alert = StockAlert(
            variant_id=variant_id,
            alert_type=alert_type,
            threshold=threshold,
            current_stock=current_stock,
            is_resolved=False
        )
        
        db.add(alert)
        await db.commit()
        await db.refresh(alert)
        
        return alert

    async def get_unresolved(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[StockAlert]:
        """
        Lấy tất cả unresolved alerts.
        """
        statement = (
            select(StockAlert)
            .options(selectinload(StockAlert.variant).selectinload(ProductVariant.product))
            .where(StockAlert.is_resolved == False)
            .order_by(StockAlert.created_at)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def resolve_alert(
        self,
        *,
        db: AsyncSession,
        alert_id: int,
        resolved_by: int
    ) -> StockAlert:
        """
        Resolve stock alert.
        """
        statement = (
            select(StockAlert)
            .options(selectinload(StockAlert.variant).selectinload(ProductVariant.product))
            .where(StockAlert.alert_id == alert_id)
        )
        result = await db.execute(statement)
        alert = result.scalar_one_or_none()
        if not alert:
            raise ValueError("Alert not found")
        
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone(timedelta(hours=7)))
        alert.resolved_by = resolved_by
        
        db.add(alert)
        await db.commit()
        result_fresh = await db.execute(statement)
        fresh_alert = result_fresh.scalar_one()
        
        return fresh_alert


inventory_transaction = CRUDInventoryTransaction(InventoryTransaction)
variant_stock = CRUDVariantStock(VariantStock)
stock_alert = CRUDStockAlert(StockAlert)