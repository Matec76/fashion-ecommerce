from typing import List, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.return_refund import (
    ReturnRequest,
    ReturnRequestCreate,
    ReturnRequestUpdate,
    ReturnItem,
    ReturnItemCreate,
    ReturnItemUpdate,
    RefundTransaction,
    RefundTransactionCreate,
    RefundTransactionUpdate,
)
from app.models.enums import (
    ReturnStatusEnum,
    RefundMethodEnum,
    OrderStatusEnum,
    ItemConditionEnum,
)
from app.crud.system import system_setting


class CRUDReturnRequest(CRUDBase[ReturnRequest, ReturnRequestCreate, ReturnRequestUpdate]):
    """CRUD operations cho ReturnRequest"""

    async def create_with_items(
        self,
        *,
        db: AsyncSession,
        return_in: ReturnRequestCreate,
        user_id: int
    ) -> ReturnRequest:
        """
        Tạo return request kèm items và CẬP NHẬT TRẠNG THÁI ĐƠN HÀNG NGAY LẬP TỨC.
        """
        from app.crud.order import order as order_crud
        
        order = await order_crud.get(db=db, id=return_in.order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to return this order"
            )
        
        if order.order_status != OrderStatusEnum.DELIVERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only return delivered orders"
            )
        
        if order.delivered_at:
            current_time = datetime.now(timezone(timedelta(hours=7)))
            delivered_at = order.delivered_at
            if delivered_at.tzinfo is None:
                delivered_at = delivered_at.replace(tzinfo=timezone.utc)

            days_since_delivery = (current_time - delivered_at).days

            return_window_val = await system_setting.get_value(
                db=db, 
                key="return_window_days", 
                default=7
            )
            
            try:
                return_window_days = int(return_window_val)
            except (ValueError, TypeError):
                return_window_days = 7

            if days_since_delivery > return_window_days:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Thời gian đổi trả đã hết hạn ({return_window_days} ngày kể từ khi nhận hàng)"
                )
            
        
        existing = await self.get_by_order(db=db, order_id=return_in.order_id)
        if existing and existing.status == ReturnStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already has a pending return request"
            )
        
        return_request = ReturnRequest(
            order_id=return_in.order_id,
            user_id=user_id,
            return_reason=return_in.return_reason,
            reason_detail=return_in.reason_detail,
            images=return_in.images,
            status=ReturnStatusEnum.PENDING,
            return_method=return_in.refund_method
        )
        
        db.add(return_request)
        await db.flush()
        
        for item_in in return_in.items:
            return_item = ReturnItem(
                return_id=return_request.return_id,
                product_id=item_in.product_id,
                variant_id=item_in.variant_id,
                quantity=item_in.quantity,
                condition=item_in.condition,
                note=item_in.note
            )
            db.add(return_item)

        order.order_status = OrderStatusEnum.RETURN_REQUESTED
        db.add(order)
        
        await db.commit()
        await db.refresh(return_request)
        
        return return_request

    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> Optional[ReturnRequest]:
        """
        Lấy return request theo order.
        """
        statement = (
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.items),
                selectinload(ReturnRequest.refunds)
            )
            .where(ReturnRequest.order_id == order_id)
            .order_by(ReturnRequest.created_at.desc())
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReturnRequest]:
        """
        Lấy return requests của user.
        """
        statement = (
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.items),
                selectinload(ReturnRequest.order),
                selectinload(ReturnRequest.refunds)
            )
            .where(ReturnRequest.user_id == user_id)
            .order_by(ReturnRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_status(
        self,
        *,
        db: AsyncSession,
        status: ReturnStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[ReturnRequest]:
        """
        Lấy return requests theo status.
        """
        statement = (
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.items),
                selectinload(ReturnRequest.user),
                selectinload(ReturnRequest.order),
                selectinload(ReturnRequest.refunds)
            )
            .where(ReturnRequest.status == status)
            .order_by(ReturnRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()
    
    async def get_all_with_details(
        self, *, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[ReturnRequest]:
        statement = (
            select(ReturnRequest)
            .options(
                selectinload(ReturnRequest.items),
                selectinload(ReturnRequest.refunds),
                selectinload(ReturnRequest.user)
            )
            .order_by(ReturnRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()


    async def approve(
        self,
        *,
        db: AsyncSession,
        return_id: int,
        refund_amount: Decimal,
        refund_method: RefundMethodEnum,
        processed_by: int,
        processed_note: Optional[str] = None,
    ) -> ReturnRequest:
        """
        Approve return request và tạo refund transaction.
        """
        return_request = await self.get(db=db, id=return_id)
        
        if not return_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return request not found"
            )
        
        if return_request.status != ReturnStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve return with status: {return_request.status}"
            )
        
        from app.crud.order import order as order_crud
        query = (
            select(order_crud.model)
            .options(selectinload(order_crud.model.payment_transactions))
            .where(order_crud.model.order_id == return_request.order_id)
        )
        order_result = await db.execute(query)
        order = order_result.scalar_one_or_none()
        if refund_amount > order.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund amount cannot exceed order total"
            )
        
        return_request.status = ReturnStatusEnum.APPROVED
        return_request.refund_amount = refund_amount
        return_request.refund_method = refund_method
        return_request.processed_note = processed_note
        return_request.processed_by = processed_by
        
        db.add(return_request)
        
        refund = RefundTransaction(
            return_id=return_id,
            payment_transaction_id=order.payment_transactions[0].transaction_id if order.payment_transactions else None,
            refund_amount=refund_amount,
            refund_method=refund_method,
            status="pending",
            initiated_by=processed_by
        )
        db.add(refund)
        
        await db.commit()
        await db.refresh(return_request)
        
        return return_request

    async def reject(
        self,
        *,
        db: AsyncSession,
        return_id: int,
        processed_by: int,
        processed_note: str,
    ) -> ReturnRequest:
        """
        Reject return request.
        """
        return_request = await self.get(db=db, id=return_id)
        
        if not return_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return request not found"
            )
        
        if return_request.status != ReturnStatusEnum.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject return with status: {return_request.status}"
            )
        
        return_request.status = ReturnStatusEnum.REJECTED
        return_request.processed_note = processed_note
        return_request.processed_by = processed_by
        
        db.add(return_request)
        await db.commit()
        await db.refresh(return_request)
        
        return return_request

    async def complete(
        self,
        *,
        db: AsyncSession,
        return_id: int
    ) -> ReturnRequest:
        """
        Mark return as completed.
        """
        return_request = await self.get(db=db, id=return_id)
        
        if not return_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Return request not found"
            )
        
        return_request.status = ReturnStatusEnum.COMPLETED
        return_request.completed_at = datetime.now(timezone(timedelta(hours=7)))
        
        db.add(return_request)
        await db.commit()
        await db.refresh(return_request)
        
        return return_request

    async def get_pending_count(
        self,
        *,
        db: AsyncSession
    ) -> int:
        """
        Đếm số return requests đang pending.
        """
        statement = select(func.count(ReturnRequest.return_id)).where(
            ReturnRequest.status == ReturnStatusEnum.PENDING
        )
        result = await db.execute(statement)
        return result.scalar_one()


class CRUDReturnItem(CRUDBase[ReturnItem, ReturnItemCreate, ReturnItemUpdate]):
    """CRUD operations cho ReturnItem"""

    async def get_by_return(
        self,
        *,
        db: AsyncSession,
        return_id: int
    ) -> List[ReturnItem]:
        """
        Lấy items của return request.
        """
        statement = (
            select(ReturnItem)
            .options(
                selectinload(ReturnItem.product),
                selectinload(ReturnItem.variant)
            )
            .where(ReturnItem.return_id == return_id)
        )
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDRefundTransaction(CRUDBase[RefundTransaction, RefundTransactionCreate, RefundTransactionUpdate]):
    """CRUD operations cho RefundTransaction"""

    async def get_by_return(
        self,
        *,
        db: AsyncSession,
        return_id: int
    ) -> List[RefundTransaction]:
        """
        Lấy refund transactions của return request.
        """
        statement = (
            select(RefundTransaction)
            .where(RefundTransaction.return_id == return_id)
            .order_by(RefundTransaction.created_at.desc())
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def process_refund(
        self,
        *,
        db: AsyncSession,
        refund_id: int,
        gateway_response: Optional[str] = None
    ) -> RefundTransaction:
        """
        Xác nhận hoàn tiền thành công -> Cập nhật Order Status & Payment Status.
        """
        refund = await self.get(db=db, id=refund_id)
        
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund transaction not found"
            )
        
        if refund.status == "processed":
            return refund

        refund.status = "processed"
        refund.processed_at = datetime.now(timezone(timedelta(hours=7)))
        refund.gateway_response = gateway_response
        db.add(refund)
        
        await return_request_crud.complete(db=db, return_id=refund.return_id)
        
        from app.crud.order import order as order_crud
        from app.models.enums import PaymentStatusEnum, OrderStatusEnum
        
        return_req = await return_request_crud.get(db=db, id=refund.return_id)
        order = await order_crud.get(db=db, id=return_req.order_id)
        
        if order:
            is_full_refund = refund.refund_amount >= order.total_amount
            
            if is_full_refund:
                update_data = {
                    "payment_status": PaymentStatusEnum.REFUNDED,
                    "order_status": OrderStatusEnum.REFUNDED
                }
            else:
                update_data = {
                    "payment_status": PaymentStatusEnum.PARTIAL_REFUNDED,
                    "order_status": OrderStatusEnum.PARTIAL_REFUNDED
                }
            
            await order_crud.update(db=db, db_obj=order, obj_in=update_data)
        
        items = await return_item_crud.get_by_return(db=db, return_id=refund.return_id)
        from app.crud.product import product_variant

        for item in items:
            if item.condition == ItemConditionEnum.UNOPENED and item.variant_id:
                await product_variant.update_stock_with_lock(
                    db=db, 
                    variant_id=item.variant_id, 
                    quantity=item.quantity, 
                    increment=True
                )

        await db.commit()
        await db.refresh(refund)
        
        return refund

    async def get_pending(
        self,
        *,
        db: AsyncSession,
        limit: int = 100
    ) -> List[RefundTransaction]:
        """
        Lấy pending refund transactions.
        """
        statement = (
            select(RefundTransaction)
            .where(RefundTransaction.status == "pending")
            .order_by(RefundTransaction.created_at)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()


return_request_crud = CRUDReturnRequest(ReturnRequest)
return_item_crud = CRUDReturnItem(ReturnItem)
refund_transaction_crud = CRUDRefundTransaction(RefundTransaction)