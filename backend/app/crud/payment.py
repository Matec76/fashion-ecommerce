from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.payment import (
    PaymentTransaction,
    PaymentTransactionCreate,
    PaymentTransactionUpdate,
    PaymentStatistics,
)
from app.models.order import Order
from app.models.enums import PaymentStatusEnum


class CRUDPaymentTransaction(CRUDBase[PaymentTransaction, PaymentTransactionCreate, PaymentTransactionUpdate]):
   
    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> List[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.order_id == order_id)
            .options(selectinload(PaymentTransaction.order))
            .order_by(PaymentTransaction.created_at.desc())
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_transaction_code(
        self,
        *,
        db: AsyncSession,
        transaction_code: str
    ) -> Optional[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.transaction_code == transaction_code)
            .order_by(PaymentTransaction.created_at.desc())
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_gateway_transaction_id(
        self,
        *,
        db: AsyncSession,
        gateway_transaction_id: str,
        gateway: Optional[str] = None
    ) -> Optional[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.gateway_transaction_id == gateway_transaction_id)
        )
        
        if gateway:
            statement = statement.where(PaymentTransaction.payment_gateway == gateway)
        
        statement = statement.order_by(PaymentTransaction.created_at.desc())
        
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_gateway(
        self,
        *,
        db: AsyncSession,
        gateway: str,
        status: Optional[PaymentStatusEnum] = None,
        limit: int = 100
    ) -> List[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.payment_gateway == gateway)
        )
        
        if status:
            statement = statement.where(PaymentTransaction.status == status)
        
        statement = statement.order_by(PaymentTransaction.created_at.desc()).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_successful_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> Optional[PaymentTransaction]:
        success_statuses = [PaymentStatusEnum.PAID, PaymentStatusEnum.PARTIAL_REFUNDED]
        
        statement = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.order_id == order_id,
                PaymentTransaction.status.in_(success_statuses)
            )
            .order_by(PaymentTransaction.created_at.desc())
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_pending_transactions(
        self,
        *,
        db: AsyncSession,
        hours: int = 24,
        gateway: Optional[str] = None,
        limit: int = 100
    ) -> List[PaymentTransaction]:
        cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(hours=hours)
        
        statement = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.status == PaymentStatusEnum.PENDING,
                PaymentTransaction.created_at < cutoff_time
            )
        )
        
        if gateway:
            statement = statement.where(PaymentTransaction.payment_gateway == gateway)
        
        statement = statement.order_by(PaymentTransaction.created_at).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_failed_transactions(
        self,
        *,
        db: AsyncSession,
        order_id: Optional[int] = None,
        gateway: Optional[str] = None,
        limit: int = 100
    ) -> List[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.status == PaymentStatusEnum.FAILED)
        )
        
        if order_id:
            statement = statement.where(PaymentTransaction.order_id == order_id)
        
        if gateway:
            statement = statement.where(PaymentTransaction.payment_gateway == gateway)
        
        statement = statement.order_by(PaymentTransaction.created_at.desc()).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_recent_pending_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int,
        minutes: int = 15
    ) -> Optional[PaymentTransaction]:
        cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(minutes=minutes)
        
        statement = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.order_id == order_id,
                PaymentTransaction.status == PaymentStatusEnum.PENDING,
                PaymentTransaction.created_at >= cutoff_time
            )
            .order_by(PaymentTransaction.created_at.desc())
        )
        
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_with_orders(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        order_by: str = "created_at",
        order_desc: bool = True
    ) -> List[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .join(Order, PaymentTransaction.order_id == Order.order_id)
            .options(selectinload(PaymentTransaction.order))
        )
        
        if filters:
            for key, value in filters.items():
                if key == "order.user_id":
                    statement = statement.where(Order.user_id == value)
                elif key == "status":
                    statement = statement.where(PaymentTransaction.status == value)
                elif key == "payment_gateway":
                    statement = statement.where(PaymentTransaction.payment_gateway == value)
                elif key == "order_id":
                    statement = statement.where(PaymentTransaction.order_id == value)
        
        order_column = getattr(PaymentTransaction, order_by, PaymentTransaction.created_at)
        if order_desc:
            statement = statement.order_by(order_column.desc())
        else:
            statement = statement.order_by(order_column.asc())
        
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def count_with_orders(
        self,
        *,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        statement = (
            select(func.count(PaymentTransaction.transaction_id))
            .select_from(PaymentTransaction)
            .join(Order, PaymentTransaction.order_id == Order.order_id)
        )
        
        if filters:
            for key, value in filters.items():
                if key == "order.user_id":
                    statement = statement.where(Order.user_id == value)
                elif key == "status":
                    statement = statement.where(PaymentTransaction.status == value)
                elif key == "payment_gateway":
                    statement = statement.where(PaymentTransaction.payment_gateway == value)
                elif key == "order_id":
                    statement = statement.where(PaymentTransaction.order_id == value)
        
        result = await db.execute(statement)
        return result.scalar_one()

    async def get_statistics(
        self,
        *,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> PaymentStatistics:
        success_statuses = [PaymentStatusEnum.PAID, PaymentStatusEnum.PARTIAL_REFUNDED]
        
        stats_statement = (
            select(
                func.count(PaymentTransaction.transaction_id).label('total_transactions'),
                func.sum(
                    case((PaymentTransaction.status.in_(success_statuses), 1), else_=0)
                ).label('successful_payments'),
                func.sum(
                    case((PaymentTransaction.status == PaymentStatusEnum.FAILED, 1), else_=0)
                ).label('failed_payments'),
                func.sum(
                    case((PaymentTransaction.status == PaymentStatusEnum.PENDING, 1), else_=0)
                ).label('pending_payments'),
                func.sum(PaymentTransaction.amount).label('total_amount'),
                func.sum(
                    case(
                        (PaymentTransaction.status.in_(success_statuses), PaymentTransaction.amount),
                        else_=0
                    )
                ).label('total_paid')
            )
            .where(
                PaymentTransaction.created_at >= start_date,
                PaymentTransaction.created_at <= end_date
            )
        )
        
        result = await db.execute(stats_statement)
        stats = result.one()
        
        total_transactions = stats.total_transactions or 0
        successful_payments = stats.successful_payments or 0
        success_rate = (successful_payments / total_transactions * 100) if total_transactions > 0 else 0
        
        gateway_statement = (
            select(
                PaymentTransaction.payment_gateway,
                func.count(PaymentTransaction.transaction_id).label('total'),
                func.sum(
                    case((PaymentTransaction.status.in_(success_statuses), 1), else_=0)
                ).label('successful'),
                func.sum(
                    case((PaymentTransaction.status == PaymentStatusEnum.FAILED, 1), else_=0)
                ).label('failed'),
                func.sum(
                    case(
                        (PaymentTransaction.status.in_(success_statuses), PaymentTransaction.amount),
                        else_=0
                    )
                ).label('amount')
            )
            .where(
                PaymentTransaction.created_at >= start_date,
                PaymentTransaction.created_at <= end_date
            )
            .group_by(PaymentTransaction.payment_gateway)
        )
        
        gateway_result = await db.execute(gateway_statement)
        gateway_rows = gateway_result.all()
        
        gateway_breakdown = {}
        for row in gateway_rows:
            gateway = row.payment_gateway or "unknown"
            gateway_breakdown[gateway] = {
                "total": int(row.total or 0),
                "successful": int(row.successful or 0),
                "failed": int(row.failed or 0),
                "amount": float(row.amount or 0)
            }
        
        return PaymentStatistics(
            total_transactions=int(total_transactions),
            successful_payments=int(successful_payments),
            failed_payments=int(stats.failed_payments or 0),
            pending_payments=int(stats.pending_payments or 0),
            total_amount=Decimal(str(stats.total_amount or 0)),
            total_paid=Decimal(str(stats.total_paid or 0)),
            success_rate=round(success_rate, 2),
            gateway_breakdown=gateway_breakdown
        )

    async def get_daily_statistics(
        self,
        *,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        success_statuses = [PaymentStatusEnum.PAID, PaymentStatusEnum.PARTIAL_REFUNDED]
        
        statement = (
            select(
                func.date(PaymentTransaction.created_at).label('date'),
                func.count(PaymentTransaction.transaction_id).label('total'),
                func.sum(
                    case((PaymentTransaction.status.in_(success_statuses), 1), else_=0)
                ).label('successful'),
                func.sum(
                    case(
                        (PaymentTransaction.status.in_(success_statuses), PaymentTransaction.amount),
                        else_=0
                    )
                ).label('amount')
            )
            .where(
                PaymentTransaction.created_at >= start_date,
                PaymentTransaction.created_at <= end_date
            )
            .group_by(func.date(PaymentTransaction.created_at))
            .order_by(func.date(PaymentTransaction.created_at))
        )
        
        result = await db.execute(statement)
        rows = result.all()
        
        daily_stats = []
        for row in rows:
            total = int(row.total or 0)
            successful = int(row.successful or 0)
            success_rate = (successful / total * 100) if total > 0 else 0
            
            daily_stats.append({
                "date": row.date.isoformat() if row.date else None,
                "total": total,
                "successful": successful,
                "amount": float(row.amount or 0),
                "success_rate": round(success_rate, 2)
            })
        
        return daily_stats

    async def get_revenue_by_gateway(
        self,
        *,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Decimal]:
        success_statuses = [PaymentStatusEnum.PAID, PaymentStatusEnum.PARTIAL_REFUNDED]
        
        statement = (
            select(
                PaymentTransaction.payment_gateway,
                func.sum(PaymentTransaction.amount).label('revenue')
            )
            .where(
                PaymentTransaction.status.in_(success_statuses),
                PaymentTransaction.created_at >= start_date,
                PaymentTransaction.created_at <= end_date
            )
            .group_by(PaymentTransaction.payment_gateway)
        )
        
        result = await db.execute(statement)
        rows = result.all()
        
        return {
            row.payment_gateway or "unknown": Decimal(str(row.revenue or 0))
            for row in rows
        }

    async def bulk_update_status(
        self,
        *,
        db: AsyncSession,
        transaction_ids: List[int],
        new_status: PaymentStatusEnum,
        notes: Optional[str] = None
    ) -> int:
        from sqlalchemy import update
        
        update_data = {"status": new_status}
        if notes:
            update_data["notes"] = notes
        if new_status == PaymentStatusEnum.PAID:
            update_data["paid_at"] = datetime.now(timezone(timedelta(hours=7)))
        
        statement = (
            update(PaymentTransaction)
            .where(PaymentTransaction.transaction_id.in_(transaction_ids))
            .values(**update_data)
        )
        
        result = await db.execute(statement)
        await db.commit()
        
        return result.rowcount

    async def get_transactions_by_ids(
        self,
        *,
        db: AsyncSession,
        transaction_ids: List[int]
    ) -> List[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.transaction_id.in_(transaction_ids))
            .order_by(PaymentTransaction.created_at.desc())
        )
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_unmatched_transactions(
        self,
        *,
        db: AsyncSession,
        gateway: str,
        hours: int = 24
    ) -> List[PaymentTransaction]:
        cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(hours=hours)
        
        statement = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.payment_gateway == gateway,
                PaymentTransaction.status == PaymentStatusEnum.PENDING,
                PaymentTransaction.created_at < cutoff_time
            )
            .order_by(PaymentTransaction.created_at)
        )
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_transactions_by_date_range(
        self,
        *,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
        status: Optional[PaymentStatusEnum] = None,
        gateway: Optional[str] = None
    ) -> List[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.created_at >= start_date,
                PaymentTransaction.created_at <= end_date
            )
        )
        
        if status:
            statement = statement.where(PaymentTransaction.status == status)
        
        if gateway:
            statement = statement.where(PaymentTransaction.payment_gateway == gateway)
        
        statement = statement.order_by(PaymentTransaction.created_at.desc())
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_duplicate_transactions(
        self,
        *,
        db: AsyncSession,
        order_id: int,
        amount: Decimal,
        gateway: str,
        minutes: int = 5
    ) -> List[PaymentTransaction]:
        cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(minutes=minutes)
        
        statement = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.order_id == order_id,
                PaymentTransaction.amount == amount,
                PaymentTransaction.payment_gateway == gateway,
                PaymentTransaction.created_at >= cutoff_time
            )
            .order_by(PaymentTransaction.created_at.desc())
        )
        
        result = await db.execute(statement)
        return list(result.scalars().all())


payment_transaction = CRUDPaymentTransaction(PaymentTransaction)