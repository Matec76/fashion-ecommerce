from typing import Optional, List
from datetime import datetime, timedelta, timezone
import json
import time
import logging

from fastapi import APIRouter, Query, status, HTTPException, Request, BackgroundTasks
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from app.api.deps import (
    SessionDep,
    CurrentUser,
    SuperUser,
    PaginationDep,
)
from app.crud.payment import payment_transaction as payment_crud
from app.crud.payment_method import payment_method as payment_method_crud
from app.crud.order import order as order_crud
from app.models.payment import (
    PaymentTransactionResponse,
    PaymentTransactionsResponse,
    PaymentRetryResponse,
    PaymentStatistics,
    RefundRequest,
    RefundResponse,
    PaymentTransactionCreate
)
from app.models.payment_method import PaymentMethodResponse
from app.models.enums import PaymentStatusEnum, OrderStatusEnum
from app.services.payos_service import PayOSService
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

_webhook_locks = {}

def user_transactions_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    user_id = kwargs.get("current_user").user_id
    pagination = kwargs.get("pagination")
    status_filter = kwargs.get("status")
    gateway = kwargs.get("gateway")
    
    page = pagination.page if pagination else 1
    page_size = pagination.page_size if pagination else 10
    
    return f"{prefix}:user:{user_id}:transactions:p{page}:s{page_size}:st{status_filter}:gw{gateway}"

def user_transaction_detail_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    user_id = kwargs.get("current_user").user_id
    transaction_id = kwargs.get("transaction_id")
    
    return f"{prefix}:user:{user_id}:transaction:{transaction_id}"

def order_transactions_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    order_id = kwargs.get("order_id")
    
    return f"{prefix}:order:{order_id}:transactions"

def payment_methods_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    return f"{prefix}:payment:methods:active"

def payment_method_detail_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    method_id = kwargs.get("method_id")
    
    return f"{prefix}:payment:method:{method_id}"

def admin_transactions_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    pagination = kwargs.get("pagination")
    status_filter = kwargs.get("status")
    gateway = kwargs.get("gateway")
    order_id = kwargs.get("order_id")
    
    page = pagination.page if pagination else 1
    page_size = pagination.page_size if pagination else 10
    
    return f"{prefix}:admin:transactions:p{page}:s{page_size}:st{status_filter}:gw{gateway}:o{order_id}"

def payment_statistics_key_builder(func, namespace: str = "", *args, **kwargs):
    prefix = FastAPICache.get_prefix() or ""
    days = kwargs.get("days", 30)
    
    return f"{prefix}:admin:statistics:days{days}"

async def invalidate_payment_caches(
    user_id: Optional[int] = None,
    order_id: Optional[int] = None,
    transaction_id: Optional[int] = None,
    clear_admin: bool = False,
    clear_stats: bool = False
):
    backend = FastAPICache.get_backend()
    prefix = FastAPICache.get_prefix() or ""
    
    if not hasattr(backend, "redis"):
        logger.warning("Redis backend not available for cache invalidation")
        return
    
    try:
        if user_id:
            patterns = [
                f"{prefix}:user:{user_id}:transactions:*",
                f"{prefix}:user:{user_id}:transaction:*",
            ]
            for pattern in patterns:
                async for key in backend.redis.scan_iter(match=pattern):
                    await backend.redis.delete(key)
        
        if order_id:
            key = f"{prefix}:order:{order_id}:transactions"
            await backend.redis.delete(key)
        
        if transaction_id:
            pattern = f"{prefix}:user:*:transaction:{transaction_id}"
            async for key in backend.redis.scan_iter(match=pattern):
                await backend.redis.delete(key)
        
        if clear_admin:
            pattern = f"{prefix}:admin:transactions:*"
            async for key in backend.redis.scan_iter(match=pattern):
                await backend.redis.delete(key)
        
        if clear_stats:
            pattern = f"{prefix}:admin:statistics:*"
            async for key in backend.redis.scan_iter(match=pattern):
                await backend.redis.delete(key)
        
        logger.info(f"Cache invalidated - user:{user_id}, order:{order_id}, txn:{transaction_id}")
        
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}", exc_info=True)

def generate_idempotency_key(order_id: int, attempt: int = 0) -> str:
    timestamp = int(time.time())
    return f"payment_{order_id}_{timestamp}_{attempt}"

def is_transaction_retryable(transaction, max_age_days: int = None) -> tuple[bool, str]:
    if max_age_days is None:
        max_age_days = settings.PAYMENT_MAX_RETRY_AGE_DAYS

    if transaction.status not in [PaymentStatusEnum.FAILED, PaymentStatusEnum.CANCELLED]:
        return False, "Can only retry failed or cancelled transactions"
    
    if transaction.created_at:
        age = datetime.now(timezone.utc) - transaction.created_at
        if age.days > max_age_days:
            return False, f"Transaction is too old (max {max_age_days} days)"
    
    return True, "OK"

async def create_audit_log(
    db: SessionDep,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    details: dict = None
):
    logger.info(
        f"AUDIT: user={user_id} action={action} resource={resource_type}:{resource_id} "
        f"details={json.dumps(details or {})}"
    )

async def invalidate_caches_task(
    user_id: Optional[int] = None,
    order_id: Optional[int] = None,
    transaction_id: Optional[int] = None,
    clear_admin: bool = False,
    clear_stats: bool = False
):
    try:
        await invalidate_payment_caches(
            user_id=user_id,
            order_id=order_id,
            transaction_id=transaction_id,
            clear_admin=clear_admin,
            clear_stats=clear_stats
        )
    except Exception as e:
        logger.error(f"Background cache invalidation failed: {e}", exc_info=True)

@router.get("/me/transactions", response_model=PaymentTransactionsResponse)
@cache(expire=60, key_builder=user_transactions_key_builder)
async def get_my_transactions(
    db: SessionDep,
    current_user: CurrentUser,
    pagination: PaginationDep,
    status: PaymentStatusEnum | None = Query(None, description="Filter by payment status"),
    gateway: str | None = Query(None, description="Filter by payment gateway"),
) -> PaymentTransactionsResponse:
    filters = {"order.user_id": current_user.user_id}
    
    if status:
        filters["status"] = status
    
    if gateway:
        filters["payment_gateway"] = gateway.lower()
    
    transactions = await payment_crud.get_multi_with_orders(
        db=db,
        skip=pagination.get_offset(),
        limit=pagination.get_limit(),
        filters=filters,
        order_by="created_at",
        order_desc=True
    )
    
    total = await payment_crud.count_with_orders(db=db, filters=filters)
    
    return PaymentTransactionsResponse(
        data=transactions,
        count=total
    )

@router.get("/me/transactions/{transaction_id}", response_model=PaymentTransactionResponse)
@cache(expire=300, key_builder=user_transaction_detail_key_builder)
async def get_my_transaction(
    db: SessionDep,
    current_user: CurrentUser,
    transaction_id: int,
) -> PaymentTransactionResponse:
    transaction = await payment_crud.get(db=db, id=transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    order = await order_crud.get(db=db, id=transaction.order_id)
    if order.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this transaction"
        )
    
    return transaction

@router.get("/orders/{order_id}/transactions", response_model=List[PaymentTransactionResponse])
@cache(expire=300, key_builder=order_transactions_key_builder)
async def get_order_transactions(
    db: SessionDep,
    current_user: CurrentUser,
    order_id: int,
) -> List[PaymentTransactionResponse]:
    order = await order_crud.get(db=db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.user_id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order's transactions"
        )
    
    transactions = await payment_crud.get_by_order(db=db, order_id=order_id)
    
    return transactions

@router.post("/transactions/{transaction_id}/retry", response_model=PaymentRetryResponse)
async def retry_failed_payment(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    transaction_id: int,
    background_tasks: BackgroundTasks,
) -> PaymentRetryResponse:
    original_txn = await payment_crud.get(db=db, id=transaction_id)
    
    if not original_txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    order = await order_crud.get(db=db, id=original_txn.order_id)
    if order.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to retry this payment"
        )
    
    can_retry, reason = is_transaction_retryable(original_txn)
    if not can_retry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason
        )
    
    if order.payment_status == PaymentStatusEnum.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid"
        )
    
    if not settings.PAYOS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment gateway is currently unavailable"
        )
    
    idempotency_key = generate_idempotency_key(order.order_id)
    
    recent_pending = await payment_crud.get_recent_pending_by_order(
        db=db,
        order_id=order.order_id,
        minutes=settings.PAYMENT_TIMEOUT_MINUTES
    )
    
    if recent_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A payment is already in progress. Please wait {settings.PAYMENT_TIMEOUT_MINUTES} minutes or use the existing payment link."
        )
    
    payos = PayOSService()
    
    new_timestamp = str(int(time.time()))
    unique_txn_code = f"{order.order_number}_{new_timestamp}"
    payos_order_code = int(time.time())
    
    new_txn_create = PaymentTransactionCreate(
        order_id=order.order_id,
        payment_method_id=order.payment_method_id,
        amount=order.total_amount,
        currency=settings.CURRENCY_CODE,
        status=PaymentStatusEnum.PENDING,
        payment_gateway="payos",
        transaction_code=unique_txn_code,
        gateway_transaction_id=str(payos_order_code),
        metadata={
            "idempotency_key": idempotency_key,
            "is_retry": True,
            "original_transaction_id": original_txn.transaction_id,
            "retry_attempt": 1
        }
    )
    
    new_transaction = await payment_crud.create(db=db, obj_in=new_txn_create)
    
    try:
        user_info = order.user_snapshot or {}
        buyer_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
        
        payment_data = await payos.create_payment_link(
            order_id=order.order_id,
            order_code=payos_order_code,
            amount=int(order.total_amount),
            description=f"Retry payment for order {order.order_number}",
            buyer_name=buyer_name or "Customer",
            buyer_email=user_info.get('email', 'customer@example.com'),
            buyer_phone=user_info.get('phone_number', ''),
            return_url=f"{settings.FRONTEND_HOST}/payment/payos/return",
            cancel_url=f"{settings.FRONTEND_HOST}/payment/payos/cancel"
        )
        
        await payment_crud.update(
            db=db,
            db_obj=new_transaction,
            obj_in={
                "payment_url": payment_data.get("checkoutUrl"),
                "qr_code": payment_data.get("qr_code"),
                "metadata": {
                    **new_transaction.metadata,
                    "payos_order_code": payment_data.get("orderCode"),
                    "payment_link_created_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        background_tasks.add_task(
            invalidate_caches_task,
            user_id=order.user_id,
            order_id=order.order_id,
            clear_stats=True
        )
        
        logger.info(
            f"Payment retry created - user:{current_user.user_id} order:{order.order_id} "
            f"txn:{new_transaction.transaction_id}"
        )
        
        return PaymentRetryResponse(
            success=True,
            message="Payment link created successfully",
            payment_url=payment_data.get("checkoutUrl"),
            transaction_id=new_transaction.transaction_id
        )
        
    except Exception as e:
        logger.error(f"PayOS error during retry: {e}", exc_info=True)
        
        await payment_crud.update(
            db=db,
            db_obj=new_transaction,
            obj_in={
                "status": PaymentStatusEnum.FAILED,
                "notes": f"Failed to create payment link: {str(e)}"
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create payment link. Please try again later."
        )

@router.get("/payos/check-status/{transaction_code}")
async def check_payos_status(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    transaction_code: str,
) -> dict:
    transaction = await payment_crud.get_by_transaction_code(
        db=db,
        transaction_code=transaction_code
    )
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    order = await order_crud.get(db=db, id=transaction.order_id)
    if order.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to check this transaction"
        )
    
    metadata = transaction.metadata or {}
    payos_order_code = metadata.get("payos_order_code")
    
    if not payos_order_code:
        return {
            "transaction_code": transaction_code,
            "status": transaction.status.value,
            "error": "PayOS order code not found in transaction metadata"
        }
    
    payos = PayOSService()
    try:
        payment_info = await payos.check_payment_status(payos_order_code)
        
        return {
            "transaction_code": transaction_code,
            "local_status": transaction.status.value,
            "payos_status": payment_info.get("status"),
            "amount": payment_info.get("amount"),
            "paid": payment_info.get("status") == "PAID",
            "synced": (payment_info.get("status") == "PAID" and 
                      transaction.status == PaymentStatusEnum.PAID)
        }
        
    except Exception as e:
        logger.error(f"Failed to check PayOS status: {e}", exc_info=True)
        return {
            "transaction_code": transaction_code,
            "local_status": transaction.status.value,
            "error": "Failed to check payment status from gateway"
        }

@router.get("/methods", response_model=List[PaymentMethodResponse])
@cache(expire=3600, key_builder=payment_methods_key_builder)
async def get_payment_methods(
    db: SessionDep,
) -> List[PaymentMethodResponse]:
    methods = await payment_method_crud.get_active(db=db)
    return methods

@router.get("/methods/{method_id}", response_model=PaymentMethodResponse)
@cache(expire=3600, key_builder=payment_method_detail_key_builder)
async def get_payment_method(
    db: SessionDep,
    method_id: int,
) -> PaymentMethodResponse:
    method = await payment_method_crud.get(db=db, id=method_id)
    
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )
    
    return method

@router.get("/admin/transactions", response_model=PaymentTransactionsResponse)
@cache(expire=60, key_builder=admin_transactions_key_builder)
async def list_all_transactions(
    db: SessionDep,
    current_user: SuperUser,
    pagination: PaginationDep,
    status: PaymentStatusEnum | None = Query(None),
    gateway: str | None = Query(None),
    order_id: int | None = Query(None),
) -> PaymentTransactionsResponse:
    filters = {}
    
    if status:
        filters["status"] = status
    
    if gateway:
        filters["payment_gateway"] = gateway.lower()
    
    if order_id:
        filters["order_id"] = order_id
    
    transactions = await payment_crud.get_multi(
        db=db,
        skip=pagination.get_offset(),
        limit=pagination.get_limit(),
        filters=filters if filters else None,
        order_by="created_at",
        order_desc=True
    )
    
    total = await payment_crud.count(db=db, filters=filters if filters else None)
    
    return PaymentTransactionsResponse(
        data=transactions,
        count=total
    )

@router.get("/admin/transactions/{transaction_id}", response_model=PaymentTransactionResponse)
async def get_transaction_admin(
    db: SessionDep,
    current_user: SuperUser,
    transaction_id: int,
) -> PaymentTransactionResponse:
    transaction = await payment_crud.get(db=db, id=transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction

@router.get("/admin/transactions/pending", response_model=List[PaymentTransactionResponse])
async def get_pending_transactions(
    db: SessionDep,
    current_user: SuperUser,
    hours: int = Query(24, ge=1, le=168, description="Look back hours"),
    gateway: str | None = Query(None, description="Filter by gateway"),
) -> List[PaymentTransactionResponse]:
    transactions = await payment_crud.get_pending_transactions(
        db=db,
        hours=hours,
        gateway=gateway,
        limit=100
    )
    
    return transactions

@router.get("/admin/transactions/failed", response_model=List[PaymentTransactionResponse])
async def get_failed_transactions(
    db: SessionDep,
    current_user: SuperUser,
    gateway: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
) -> List[PaymentTransactionResponse]:
    transactions = await payment_crud.get_failed_transactions(
        db=db,
        gateway=gateway,
        limit=limit
    )
    
    return transactions

@router.get("/admin/transactions/gateway/{gateway}", response_model=List[PaymentTransactionResponse])
async def get_transactions_by_gateway(
    db: SessionDep,
    current_user: SuperUser,
    gateway: str,
    status: PaymentStatusEnum | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
) -> List[PaymentTransactionResponse]:
    transactions = await payment_crud.get_by_gateway(
        db=db,
        gateway=gateway,
        status=status,
        limit=limit
    )
    
    return transactions

@router.patch("/admin/transactions/{transaction_id}/status", response_model=PaymentTransactionResponse)
async def update_transaction_status(
    *,
    db: SessionDep,
    current_user: SuperUser,
    transaction_id: int,
    new_status: PaymentStatusEnum,
    notes: str | None = None,
    background_tasks: BackgroundTasks,
) -> PaymentTransactionResponse:
    transaction = await payment_crud.get(db=db, id=transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    old_status = transaction.status
    
    update_data = {
        "status": new_status,
        "notes": notes or transaction.notes
    }
    
    if new_status == PaymentStatusEnum.PAID and not transaction.paid_at:
        update_data["paid_at"] = datetime.now(timezone.utc)
    
    updated_transaction = await payment_crud.update(
        db=db,
        db_obj=transaction,
        obj_in=update_data
    )
    
    order = await order_crud.get(db=db, id=transaction.order_id)
    if new_status == PaymentStatusEnum.PAID and order.payment_status != PaymentStatusEnum.PAID:
        await order_crud.update(
            db=db,
            db_obj=order,
            obj_in={
                "payment_status": PaymentStatusEnum.PAID,
                "order_status": OrderStatusEnum.CONFIRMED
            }
        )
    
    await create_audit_log(
        db=db,
        user_id=current_user.user_id,
        action="update_transaction_status",
        resource_type="payment_transaction",
        resource_id=transaction_id,
        details={
            "old_status": old_status.value,
            "new_status": new_status.value,
            "notes": notes
        }
    )
    
    background_tasks.add_task(
        invalidate_caches_task,
        user_id=order.user_id,
        order_id=order.order_id,
        transaction_id=transaction_id,
        clear_admin=True,
        clear_stats=True
    )
    
    logger.info(
        f"Transaction status updated - admin:{current_user.user_id} txn:{transaction_id} "
        f"{old_status.value} -> {new_status.value}"
    )
    
    return updated_transaction

@router.get("/admin/search", response_model=List[PaymentTransactionResponse])
async def search_transactions(
    db: SessionDep,
    current_user: SuperUser,
    q: str = Query(..., min_length=3, description="Search by transaction code or gateway ID"),
) -> List[PaymentTransactionResponse]:
    by_code = await payment_crud.get_by_transaction_code(db=db, transaction_code=q)
    
    by_gateway_id = await payment_crud.get_by_gateway_transaction_id(
        db=db,
        gateway_transaction_id=q
    )
    
    results = []
    seen_ids = set()
    
    for txn in [by_code, by_gateway_id]:
        if txn and txn.transaction_id not in seen_ids:
            results.append(txn)
            seen_ids.add(txn.transaction_id)
    
    return results

@router.get("/admin/statistics", response_model=PaymentStatistics)
@cache(expire=300, key_builder=payment_statistics_key_builder)
async def get_payment_statistics(
    db: SessionDep,
    current_user: SuperUser,
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
) -> PaymentStatistics:
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    stats = await payment_crud.get_statistics(
        db=db,
        start_date=start_date,
        end_date=datetime.now(timezone.utc)
    )
    
    return stats

@router.post("/admin/refunds", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
async def request_refund(
    *,
    db: SessionDep,
    current_user: SuperUser,
    refund_in: RefundRequest,
    background_tasks: BackgroundTasks,
) -> RefundResponse:
    transaction = await payment_crud.get(db=db, id=refund_in.transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.status not in [PaymentStatusEnum.PAID, PaymentStatusEnum.PARTIAL_REFUNDED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund paid or partially refunded transactions"
        )
    
    if refund_in.refund_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount must be greater than 0"
        )
    
    if refund_in.refund_amount > transaction.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount cannot exceed transaction amount"
        )
    
    if not current_user.is_superuser and refund_in.refund_amount > settings.PAYMENT_MAX_REFUND_AMOUNT_PER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Refund amount exceeds your limit of {settings.PAYMENT_MAX_REFUND_AMOUNT_PER_ADMIN}"
        )
    
    metadata = transaction.metadata or {}
    previous_refunds = metadata.get("refunds", [])
    total_refunded = sum(r.get("amount", 0) for r in previous_refunds)
    
    current_total_refunded = total_refunded + refund_in.refund_amount
    
    if current_total_refunded > transaction.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Total refund amount would exceed transaction amount. Already refunded: {total_refunded}"
        )
    
    is_full_refund = current_total_refunded == transaction.amount
    
    if is_full_refund:
        new_status = PaymentStatusEnum.REFUNDED
    else:
        new_status = PaymentStatusEnum.PARTIAL_REFUNDED
    
    refund_record = {
        "refund_id": int(time.time()),
        "amount": float(refund_in.refund_amount),
        "reason": refund_in.reason,
        "refunded_by": current_user.user_id,
        "refunded_by_email": current_user.email,
        "refunded_at": datetime.now(timezone.utc).isoformat()
    }
    
    previous_refunds.append(refund_record)
    
    notes = transaction.notes or ""
    refund_note = (
        f"\n[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}] "
        f"Refund: {refund_in.refund_amount} {transaction.currency} "
        f"by {current_user.email}. Reason: {refund_in.reason}"
    )
    
    await payment_crud.update(
        db=db,
        db_obj=transaction,
        obj_in={
            "status": new_status,
            "notes": notes + refund_note,
            "metadata": {
                **metadata,
                "refunds": previous_refunds,
                "total_refunded": float(current_total_refunded),
                "is_partially_refunded": not is_full_refund
            }
        }
    )
    
    order = await order_crud.get(db=db, id=transaction.order_id)
    if order:
        if is_full_refund:
            await order_crud.update(
                db=db,
                db_obj=order,
                obj_in={
                    "payment_status": PaymentStatusEnum.REFUNDED,
                    "order_status": OrderStatusEnum.CANCELLED
                }
            )
        else:
             await order_crud.update(
                db=db,
                db_obj=order,
                obj_in={
                    "payment_status": PaymentStatusEnum.PARTIAL_REFUNDED
                }
            )
    
    await create_audit_log(
        db=db,
        user_id=current_user.user_id,
        action="refund_transaction",
        resource_type="payment_transaction",
        resource_id=refund_in.transaction_id,
        details={
            "refund_amount": float(refund_in.refund_amount),
            "reason": refund_in.reason,
            "is_full_refund": is_full_refund,
            "total_refunded": float(current_total_refunded)
        }
    )
    
    background_tasks.add_task(
        invalidate_caches_task,
        user_id=order.user_id if order else None,
        order_id=order.order_id if order else None,
        transaction_id=refund_in.transaction_id,
        clear_admin=True,
        clear_stats=True
    )
    
    logger.info(
        f"Refund processed - admin:{current_user.user_id} txn:{refund_in.transaction_id} "
        f"amount:{refund_in.refund_amount} full:{is_full_refund}"
    )
    
    return RefundResponse(
        refund_id=refund_record["refund_id"],
        transaction_id=refund_in.transaction_id,
        refund_amount=refund_in.refund_amount,
        status="completed" if is_full_refund else "partial",
        created_at=datetime.now(timezone.utc)
    )

@router.post("/webhooks/payos")
async def payos_webhook_handler(
    *,
    db: SessionDep,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    payos = PayOSService()
    
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body"
        )
    
    signature = request.headers.get("x-signature", "")
    webhook_data = body.get("data", {})
    
    is_valid = payos.verify_webhook_signature(webhook_data, signature)
    
    if not is_valid:
        logger.warning(f"Invalid webhook signature: {signature[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    payos_order_code = str(webhook_data.get("orderCode"))
    reference = webhook_data.get("reference")
    transaction_datetime = webhook_data.get("transactionDateTime")
    status_code = webhook_data.get("code")
    
    lock_key = f"webhook_{payos_order_code}_{status_code}"
    
    if lock_key in _webhook_locks:
        lock_time = _webhook_locks[lock_key]
        if (datetime.now(timezone.utc) - lock_time).seconds < settings.PAYMENT_WEBHOOK_LOCK_TIMEOUT:
            logger.info(f"Webhook already being processed: {lock_key}")
            return {"message": "Already processing", "processed": False}
    
    _webhook_locks[lock_key] = datetime.now(timezone.utc)
    
    try:
        transaction = await payment_crud.get_by_gateway_transaction_id(
            db=db,
            gateway_transaction_id=payos_order_code
        )
        
        if not transaction:
            logger.warning(f"Transaction not found for PayOS order: {payos_order_code}")
            return {"message": "Transaction not found", "processed": False}
        
        order = await order_crud.get(db=db, id=transaction.order_id)
        if not order:
            logger.error(f"Order not found for transaction: {transaction.transaction_id}")
            return {"message": "Order not found", "processed": False}
        
        if status_code == "00":
            if transaction.status == PaymentStatusEnum.PAID:
                logger.info(f"Transaction already marked as paid: {transaction.transaction_id}")
                return {
                    "message": "Already processed",
                    "processed": True,
                    "order_id": order.order_id
                }
            
            await payment_crud.update(
                db=db,
                db_obj=transaction,
                obj_in={
                    "status": PaymentStatusEnum.PAID,
                    "gateway_transaction_id": reference,
                    "paid_at": datetime.now(timezone.utc),
                    "notes": "Payment completed successfully via PayOS webhook",
                    "gateway_response": json.dumps(webhook_data),
                    "metadata": {
                        **(transaction.metadata or {}),
                        "counter_account_name": webhook_data.get("counterAccountName"),
                        "counter_account_number": webhook_data.get("counterAccountNumber"),
                        "transaction_datetime": transaction_datetime,
                        "webhook_processed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            await order_crud.update(
                db=db,
                db_obj=order,
                obj_in={
                    "payment_status": PaymentStatusEnum.PAID,
                    "order_status": OrderStatusEnum.CONFIRMED
                }
            )
            
            background_tasks.add_task(
                invalidate_caches_task,
                user_id=order.user_id,
                order_id=order.order_id,
                transaction_id=transaction.transaction_id,
                clear_admin=True,
                clear_stats=True
            )
            
            logger.info(
                f"Payment webhook processed successfully - order:{order.order_id} "
                f"txn:{transaction.transaction_id} payos:{payos_order_code}"
            )
            
            return {
                "message": "Payment processed successfully",
                "processed": True,
                "order_id": order.order_id,
                "transaction_id": transaction.transaction_id
            }
        
        else:
            if transaction.status == PaymentStatusEnum.FAILED:
                logger.info(f"Transaction already marked as failed: {transaction.transaction_id}")
                return {
                    "message": "Already processed",
                    "processed": True,
                    "order_id": order.order_id
                }
            
            await payment_crud.update(
                db=db,
                db_obj=transaction,
                obj_in={
                    "status": PaymentStatusEnum.FAILED,
                    "gateway_transaction_id": reference,
                    "notes": f"Payment failed via PayOS webhook. Code: {status_code}",
                    "gateway_response": json.dumps(webhook_data),
                    "metadata": {
                        **(transaction.metadata or {}),
                        "failure_code": status_code,
                        "webhook_processed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            await order_crud.update(
                db=db,
                db_obj=order,
                obj_in={"payment_status": PaymentStatusEnum.FAILED}
            )
            
            background_tasks.add_task(
                invalidate_caches_task,
                user_id=order.user_id,
                order_id=order.order_id,
                transaction_id=transaction.transaction_id,
                clear_stats=True
            )
            
            logger.warning(
                f"Payment webhook failed - order:{order.order_id} "
                f"txn:{transaction.transaction_id} code:{status_code}"
            )
            
            return {
                "message": "Payment failed",
                "processed": True,
                "order_id": order.order_id,
                "transaction_id": transaction.transaction_id,
                "error_code": status_code
            }
    
    finally:
        pass

@router.get("/health")
async def payment_health_check(
    db: SessionDep,
) -> dict:
    health_status = {
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        await payment_crud.get_multi(db=db, limit=1)
        health_status["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["database_error"] = str(e)
    
    try:
        active_methods = await payment_method_crud.get_active(db=db)
        health_status["payment_methods"] = {
            "status": "healthy",
            "active_count": len(active_methods)
        }
    except Exception as e:
        logger.error(f"Payment methods health check failed: {e}")
        health_status["payment_methods"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    try:
        if settings.PAYOS_ENABLED:
            health_status["payos"] = "enabled"
        else:
            health_status["payos"] = "disabled"
    except Exception as e:
        health_status["payos"] = "unknown"
    
    if health_status.get("database") != "healthy":
        health_status["status"] = "degraded"
    
    return health_status