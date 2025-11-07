"""
CRUD operations cho PaymentTransaction model.

Quản lý giao dịch thanh toán (create, update status, upsert from webhook).
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.payment import (
    PaymentTransaction,
    PaymentTransactionCreate,
    PaymentTransactionUpdate,
)
from app.models.enums import PaymentStatusEnum


class CRUDPaymentTransaction(CRUDBase[PaymentTransaction, PaymentTransactionCreate, PaymentTransactionUpdate]):
    """CRUD operations cho PaymentTransaction"""

    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> List[PaymentTransaction]:
        """
        Lấy tất cả payment transactions của order.
        
        Args:
            db: Database session
            order_id: Order ID
            
        Returns:
            List PaymentTransaction instances
        """
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.order_id == order_id)
            .order_by(PaymentTransaction.created_at.desc())
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_transaction_code(
        self,
        *,
        db: AsyncSession,
        transaction_code: str
    ) -> Optional[PaymentTransaction]:
        """
        Lấy payment transaction theo transaction_code.
        
        Args:
            db: Database session
            transaction_code: Transaction code từ gateway
            
        Returns:
            PaymentTransaction instance hoặc None
        """
        statement = select(PaymentTransaction).where(
            PaymentTransaction.transaction_code == transaction_code
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create_transaction(
        self,
        *,
        db: AsyncSession,
        order_id: int,
        transaction_code: str,
        payment_method: str,
        payment_gateway: str,
        amount: Decimal,
        currency: str = "VND"
    ) -> PaymentTransaction:
        """
        Tạo payment transaction mới.
        
        Args:
            db: Database session
            order_id: Order ID
            transaction_code: Transaction code từ gateway
            payment_method: Payment method (vnpay, momo, cod, etc.)
            payment_gateway: Gateway name
            amount: Số tiền
            currency: Đơn vị tiền tệ
            
        Returns:
            PaymentTransaction instance
        """
        transaction = PaymentTransaction(
            order_id=order_id,
            transaction_code=transaction_code,
            payment_method=payment_method,
            payment_gateway=payment_gateway,
            amount=amount,
            currency=currency,
            status=PaymentStatusEnum.PENDING
        )
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    async def update_status(
        self,
        *,
        db: AsyncSession,
        transaction_id: int,
        status: PaymentStatusEnum,
        gateway_response: Optional[str] = None
    ) -> PaymentTransaction:
        """
        Cập nhật trạng thái payment transaction.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            status: Payment status mới
            gateway_response: Response từ gateway (JSON string)
            
        Returns:
            PaymentTransaction instance đã cập nhật
        """
        transaction = await self.get(db=db, id=transaction_id)
        transaction.status = status
        
        if gateway_response:
            transaction.gateway_response = gateway_response
        
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    async def upsert_from_webhook(
        self,
        *,
        db: AsyncSession,
        transaction_code: str,
        order_id: int,
        payment_method: str,
        payment_gateway: str,
        amount: Decimal,
        status: PaymentStatusEnum,
        gateway_response: str,
        currency: str = "VND"
    ) -> PaymentTransaction:
        """
        Upsert payment transaction từ webhook (idempotent).
        
        Args:
            db: Database session
            transaction_code: Transaction code từ gateway
            order_id: Order ID
            payment_method: Payment method
            payment_gateway: Gateway name
            amount: Số tiền
            status: Payment status
            gateway_response: Response từ gateway
            currency: Đơn vị tiền tệ
            
        Returns:
            PaymentTransaction instance
        """
        # Kiểm tra đã tồn tại chưa
        existing = await self.get_by_transaction_code(
            db=db,
            transaction_code=transaction_code
        )
        
        if existing:
            # Cập nhật
            existing.status = status
            existing.gateway_response = gateway_response
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing
        else:
            # Tạo mới
            transaction = PaymentTransaction(
                order_id=order_id,
                transaction_code=transaction_code,
                payment_method=payment_method,
                payment_gateway=payment_gateway,
                amount=amount,
                currency=currency,
                status=status,
                gateway_response=gateway_response
            )
            db.add(transaction)
            await db.commit()
            await db.refresh(transaction)
            return transaction

    async def get_successful_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> Optional[PaymentTransaction]:
        """
        Lấy payment transaction thành công của order.
        
        Args:
            db: Database session
            order_id: Order ID
            
        Returns:
            PaymentTransaction instance hoặc None
        """
        statement = select(PaymentTransaction).where(
            PaymentTransaction.order_id == order_id,
            PaymentTransaction.status == PaymentStatusEnum.PAID
        ).order_by(PaymentTransaction.created_at.desc())
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_pending_transactions(
        self,
        *,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 100
    ) -> List[PaymentTransaction]:
        """
        Lấy transactions đang pending quá lâu (cần check lại).
        
        Args:
            db: Database session
            hours: Số giờ pending
            limit: Limit
            
        Returns:
            List PaymentTransaction instances
        """
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        statement = (
            select(PaymentTransaction)
            .where(
                PaymentTransaction.status == PaymentStatusEnum.PENDING,
                PaymentTransaction.created_at < cutoff_time
            )
            .order_by(PaymentTransaction.created_at)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()


# Singleton instance
payment_transaction = CRUDPaymentTransaction(PaymentTransaction)
