from typing import List, Optional
from decimal import Decimal
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.payment_method import (
    PaymentMethod,
    PaymentMethodCreate,
    PaymentMethodUpdate,
)
from app.models.payment import PaymentTransaction
from app.models.enums import PaymentMethodType, PaymentStatusEnum, ProcessingFeeType

class CRUDPaymentMethod(CRUDBase[PaymentMethod, PaymentMethodCreate, PaymentMethodUpdate]):
    async def get_active(self, *, db: AsyncSession) -> List[PaymentMethod]:
        statement = (
            select(PaymentMethod)
            .where(PaymentMethod.is_active.is_(True))
            .order_by(PaymentMethod.display_order, PaymentMethod.method_name)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())
    
    async def get_by_code(self, *, db: AsyncSession, method_code: str) -> Optional[PaymentMethod]:
        statement = select(PaymentMethod).where(PaymentMethod.method_code == method_code)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_by_name(self, *, db: AsyncSession, method_name: str) -> Optional[PaymentMethod]:
        statement = select(PaymentMethod).where(PaymentMethod.method_name == method_name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_cod(self, *, db: AsyncSession) -> Optional[PaymentMethod]:
        return await self.get_by_code(db=db, method_code=PaymentMethodType.COD.value)
    
    async def get_payos(self, *, db: AsyncSession) -> Optional[PaymentMethod]:
        return await self.get_by_code(db=db, method_code=PaymentMethodType.BANK_TRANSFER.value)
    
    async def get_bank_transfer(self, *, db: AsyncSession) -> Optional[PaymentMethod]:
        return await self.get_payos(db=db)
    
    async def toggle_active(self, *, db: AsyncSession, id: int) -> Optional[PaymentMethod]:
        payment_method = await self.get(db=db, id=id)
        if not payment_method:
            return None
        
        payment_method.is_active = not payment_method.is_active
        db.add(payment_method)
        await db.commit()
        await db.refresh(payment_method)
        return payment_method
    
    async def validate_for_order(
        self, *, db: AsyncSession, payment_method_id: int, order_amount: Decimal
    ) -> tuple[bool, Optional[str]]:
        payment_method = await self.get(db=db, id=payment_method_id)
        
        if not payment_method:
            return False, "Payment method not found"
        
        if not payment_method.is_active:
            return False, f"Payment method '{payment_method.method_name}' is currently unavailable"
        
        if payment_method.min_order_amount and order_amount < payment_method.min_order_amount:
            return False, f"Order amount must be at least {payment_method.min_order_amount:,.0f} VND"
            
        if payment_method.max_order_amount and order_amount > payment_method.max_order_amount:
            return False, f"Order amount exceeds limit of {payment_method.max_order_amount:,.0f} VND"
        
        return True, None
    
    async def calculate_processing_fee(
        self, *, db: AsyncSession, payment_method_id: int, order_amount: Decimal
    ) -> Decimal:
        payment_method = await self.get(db=db, id=payment_method_id)
        
        if not payment_method:
            return Decimal("0.00")
        
        if payment_method.processing_fee_type == ProcessingFeeType.PERCENTAGE:
            fee = (order_amount * payment_method.processing_fee) / Decimal("100")
        else:
            fee = payment_method.processing_fee
        
        return fee.quantize(Decimal("0.01"))
    
    async def get_statistics(self, *, db: AsyncSession, payment_method_id: int) -> dict:
        statement = (
            select(
                func.count(PaymentTransaction.transaction_id).label('total_transactions'),
                func.count(case((PaymentTransaction.status == PaymentStatusEnum.PAID, 1), else_=None)).label('successful_transactions'),
                func.count(case((PaymentTransaction.status == PaymentStatusEnum.FAILED, 1), else_=None)).label('failed_transactions'),
                func.coalesce(func.sum(case((PaymentTransaction.status == PaymentStatusEnum.PAID, PaymentTransaction.amount), else_=0)), 0).label('total_amount')
            )
            .where(PaymentTransaction.payment_method_id == payment_method_id)
        )
        
        result = await db.execute(statement)
        stats = result.first()
        
        if not stats or stats.total_transactions == 0:
            return {
                'total_transactions': 0, 'successful_transactions': 0, 'failed_transactions': 0,
                'total_amount': Decimal("0.00"), 'success_rate': 0.0
            }
        
        success_rate = (stats.successful_transactions / stats.total_transactions * 100)
        
        return {
            'total_transactions': stats.total_transactions,
            'successful_transactions': stats.successful_transactions,
            'failed_transactions': stats.failed_transactions,
            'total_amount': Decimal(str(stats.total_amount)),
            'success_rate': round(success_rate, 2)
        }
    
    async def get_most_used(self, *, db: AsyncSession, limit: int = 5) -> List[tuple[PaymentMethod, int]]:
        statement = (
            select(PaymentMethod, func.count(PaymentTransaction.transaction_id))
            .join(PaymentTransaction, PaymentMethod.payment_method_id == PaymentTransaction.payment_method_id)
            .group_by(PaymentMethod.payment_method_id)
            .order_by(func.count(PaymentTransaction.transaction_id).desc())
            .limit(limit)
        )
        result = await db.execute(statement)
        return [(row[0], row[1]) for row in result.all()]

payment_method = CRUDPaymentMethod(PaymentMethod)