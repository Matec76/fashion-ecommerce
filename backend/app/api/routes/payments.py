from typing import Optional, List
from datetime import datetime, timedelta, timezone
import json
import time
import logging

from fastapi import APIRouter, Query, status, HTTPException, Request, BackgroundTasks, Depends
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from app.api.deps import (
    SessionDep,
    CurrentUser,
    PaginationDep,
    require_permission,
)
from app.crud.payment import payment_transaction as payment_crud
from app.crud.payment_method import payment_method as payment_method_crud
from app.crud.order import order as order_crud
from app.crud.cart import cart as cart_crud
from app.crud.product import product_variant, product as product_crud
from app.models.payment import (
    PaymentTransactionResponse,
    PaymentTransactionsResponse,
    PaymentStatistics,
    RefundRequest,
    RefundResponse,
)
from app.models.payment_method import PaymentMethodResponse
from app.models.enums import PaymentStatusEnum, OrderStatusEnum
from app.services.payos_service import PayOSService
from app.core.config import settings
from app.models.user import User
from app.crud.system import system_setting

router = APIRouter()
logger = logging.getLogger(__name__)

_webhook_locks = {}

def user_transactions_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho danh sách giao dịch của người dùng hiện tại.
    """
    prefix = FastAPICache.get_prefix() or ""
    user_id = kwargs.get("current_user").user_id
    pagination = kwargs.get("pagination")
    status_filter = kwargs.get("status")
    gateway = kwargs.get("gateway")
    
    page = pagination.page if pagination else 1
    page_size = pagination.page_size if pagination else 10
    
    return f"{prefix}:user:{user_id}:transactions:p{page}:s{page_size}:st{status_filter}:gw{gateway}"

def user_transaction_detail_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho thông tin chi tiết của một giao dịch cụ thể.
    """
    prefix = FastAPICache.get_prefix() or ""
    user_id = kwargs.get("current_user").user_id
    transaction_id = kwargs.get("transaction_id")
    
    return f"{prefix}:user:{user_id}:transaction:{transaction_id}"

def order_transactions_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho các giao dịch liên quan đến một đơn hàng.
    """
    prefix = FastAPICache.get_prefix() or ""
    order_id = kwargs.get("order_id")
    
    return f"{prefix}:order:{order_id}:transactions"

def payment_methods_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho danh sách các phương thức thanh toán đang hoạt động.
    """
    prefix = FastAPICache.get_prefix() or ""
    return f"{prefix}:payment:methods:active"

def payment_method_detail_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho thông tin chi tiết của một phương thức thanh toán.
    """
    prefix = FastAPICache.get_prefix() or ""
    method_id = kwargs.get("method_id")
    
    return f"{prefix}:payment:method:{method_id}"

def admin_transactions_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho Admin khi truy vấn toàn bộ giao dịch trên hệ thống.
    """
    prefix = FastAPICache.get_prefix() or ""
    pagination = kwargs.get("pagination")
    status_filter = kwargs.get("status")
    gateway = kwargs.get("gateway")
    order_id = kwargs.get("order_id")
    
    page = pagination.page if pagination else 1
    page_size = pagination.page_size if pagination else 10
    
    return f"{prefix}:admin:transactions:p{page}:s{page_size}:st{status_filter}:gw{gateway}:o{order_id}"

def payment_statistics_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho các báo cáo thống kê thanh toán.
    """
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
    """
    Thực hiện xóa cache liên quan đến thanh toán dựa trên các điều kiện xác định.
    """
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
    """
    Tạo khóa idempotency để đảm bảo một yêu cầu thanh toán không bị xử lý trùng lặp.
    """
    timestamp = int(time.time())
    return f"payment_{order_id}_{timestamp}_{attempt}"

def is_transaction_retryable(transaction, max_age_days: int = None) -> tuple[bool, str]:
    """
    Kiểm tra xem một giao dịch thanh toán thất bại có đủ điều kiện để thực hiện lại hay không.
    """
    if max_age_days is None:
        max_age_days = settings.PAYMENT_MAX_RETRY_AGE_DAYS

    if transaction.status not in [PaymentStatusEnum.FAILED, PaymentStatusEnum.CANCELLED]:
        return False, "Can only retry failed or cancelled transactions"
    
    if transaction.created_at:
        age = datetime.now(timezone(timedelta(hours=7))) - transaction.created_at
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
    """
    Ghi nhật ký kiểm toán (audit log) cho các hành động thay đổi dữ liệu thanh toán quan trọng.
    """
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
    """
    Task chạy ngầm để thực hiện việc xóa cache thanh toán sau khi dữ liệu được cập nhật.
    """
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
    """
    Lấy danh sách lịch sử giao dịch thanh toán của người dùng đang đăng nhập.
    """
    filters = {"order.user_id": current_user.user_id}
    
    if status:
        filters["status"] = status
    
    if gateway:
        filters["payment_gateway"] = gateway
    
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
    """
    Xem thông tin chi tiết về một giao dịch thanh toán cụ thể của người dùng.
    """
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
    """
    Lấy toàn bộ các giao dịch thanh toán liên quan đến một đơn hàng cụ thể.
    """
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


@router.get("/payos/check-status/{transaction_code}")
async def check_payos_status(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    transaction_code: str,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Kiểm tra trạng thái thanh toán từ PayOS cho một giao dịch và đồng bộ hóa kết quả vào hệ thống.
    """
    transaction = await payment_crud.get_by_transaction_code(
        db=db,
        transaction_code=transaction_code
    )
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    order = await order_crud.get_with_details(db=db, id=transaction.order_id)
    if order.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to check this transaction"
        )
    
    payment_metadata = transaction.payment_metadata or {}
    payos_order_code = payment_metadata.get("payos_order_code")
    
    if not payos_order_code:
        return {
            "transaction_code": transaction_code,
            "status": transaction.status.value,
            "error": "PayOS order code not found in transaction payment_metadata"
        }
    
    payos = PayOSService()
    try:
        payment_info = await payos.check_payment_status(payos_order_code)
        payos_status = payment_info.get("status")

        is_synced = False
        if payos_status == "PAID" and transaction.status != PaymentStatusEnum.PAID:
            await payment_crud.update(
                db=db,
                db_obj=transaction,
                obj_in={
                    "status": PaymentStatusEnum.PAID,
                    "paid_at": datetime.now(timezone(timedelta(hours=7))),
                    "notes": "Payment synced via check-status API",
                    "gateway_response": json.dumps(payment_info)
                }
            )
            
            if order:

                purchased_variant_ids = [item.variant_id for item in order.items]
                await cart_crud.remove_items_after_checkout(
                    db=db,
                    user_id=order.user_id,
                    variant_ids=purchased_variant_ids
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
            is_synced = True
        
        return {
            "transaction_code": transaction_code,
            "local_status": transaction.status.value,
            "payos_status": payos_status, 
            "amount": payment_info.get("amount"),
            "paid": payos_status == "PAID",          
            "synced": is_synced             
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
    """
    Lấy danh sách các phương thức thanh toán đang được hệ thống hỗ trợ.
    """
    methods = await payment_method_crud.get_active(db=db)
    return methods

@router.get("/methods/{method_id}", response_model=PaymentMethodResponse)
@cache(expire=3600, key_builder=payment_method_detail_key_builder)
async def get_payment_method(
    db: SessionDep,
    method_id: int,
) -> PaymentMethodResponse:
    """
    Xem thông tin chi tiết cấu hình của một phương thức thanh toán theo ID.
    """
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
    pagination: PaginationDep,
    status: PaymentStatusEnum | None = Query(None),
    gateway: str | None = Query(None),
    order_id: int | None = Query(None),
    current_user: User = Depends(require_permission("payment.view")),
) -> PaymentTransactionsResponse:
    """
    Liệt kê và quản lý toàn bộ các giao dịch thanh toán trên hệ thống (Dành cho Admin).
    """
    filters = {}
    
    if status:
        filters["status"] = status
    
    if gateway:
        filters["payment_gateway"] = gateway
    
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
    transaction_id: int,
    current_user: User = Depends(require_permission("payment.view")),
) -> PaymentTransactionResponse:
    """
    Xem thông tin chi tiết của một giao dịch thanh toán bất kỳ (Dành cho Admin).
    """
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
    hours: int = Query(24, ge=1, le=168, description="Look back hours"),
    gateway: str | None = Query(None, description="Filter by gateway"),
    current_user: User = Depends(require_permission("payment.view")),
) -> List[PaymentTransactionResponse]:
    """
    Lấy danh sách các giao dịch đang ở trạng thái chờ xử lý (Dành cho Admin).
    """
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
    gateway: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_permission("payment.view")),
) -> List[PaymentTransactionResponse]:
    """
    Lấy danh sách các giao dịch thanh toán đã bị lỗi hoặc thất bại (Dành cho Admin).
    """
    transactions = await payment_crud.get_failed_transactions(
        db=db,
        gateway=gateway,
        limit=limit
    )
    
    return transactions

@router.get("/admin/transactions/gateway/{gateway}", response_model=List[PaymentTransactionResponse])
async def get_transactions_by_gateway(
    db: SessionDep,
    gateway: str,
    status: PaymentStatusEnum | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_permission("payment.view")),
) -> List[PaymentTransactionResponse]:
    """
    Lọc danh sách giao dịch dựa theo cổng thanh toán gateway (Dành cho Admin).
    """
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
    transaction_id: int,
    new_status: PaymentStatusEnum,
    notes: str | None = None,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("payment.update")),
) -> PaymentTransactionResponse:
    """
    Cập nhật thủ công trạng thái của một giao dịch thanh toán (Dành cho Admin).
    """
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
        update_data["paid_at"] = datetime.now(timezone(timedelta(hours=7)))
    
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
    q: str = Query(..., min_length=3, description="Search by transaction code or gateway ID"),
    current_user: User = Depends(require_permission("payment.view")),
) -> List[PaymentTransactionResponse]:
    """
    Tìm kiếm nhanh giao dịch theo mã giao dịch nội bộ hoặc mã từ cổng gateway.
    """
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
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    current_user: User = Depends(require_permission("analytics.view")),
) -> PaymentStatistics:
    """
    Lấy dữ liệu báo cáo thống kê tình hình thanh toán trong một khoảng thời gian xác định.
    """
    start_date = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=days)
    
    stats = await payment_crud.get_statistics(
        db=db,
        start_date=start_date,
        end_date=datetime.now(timezone(timedelta(hours=7)))
    )
    
    return stats

@router.post("/admin/refunds", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
async def request_refund(
    *,
    db: SessionDep,
    refund_in: RefundRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("payment.refund")),
) -> RefundResponse:
    """
    Xử lý yêu cầu hoàn tiền cho một giao dịch đã thanh toán thành công (Dành cho Admin).
    """
    transaction = await payment_crud.get(db=db, id=refund_in.transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    allowed_statuses = [PaymentStatusEnum.PAID, PaymentStatusEnum.REFUNDED]
    if transaction.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Can only refund transactions that are PAID or previously REFUNDED"
        )
    
    if refund_in.refund_amount <= 0:
        raise HTTPException(status_code=400, detail="Refund amount must be greater than 0")
        
    if not current_user.is_superuser and refund_in.refund_amount > settings.PAYMENT_MAX_REFUND_AMOUNT_PER_ADMIN:
        raise HTTPException(status_code=403, detail="Refund amount exceeds limit")

    payment_metadata = transaction.payment_metadata or {}
    previous_refunds = payment_metadata.get("refunds", [])
    total_refunded = sum(r.get("amount", 0) for r in previous_refunds)
    
    current_total_refunded = total_refunded + refund_in.refund_amount
    
    if current_total_refunded > transaction.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Total refund ({current_total_refunded}) exceeds transaction amount ({transaction.amount})"
        )
    
    is_full_refund = current_total_refunded == transaction.amount
    
    new_payment_status = PaymentStatusEnum.PARTIAL_REFUNDED
    
    refund_record = {
        "refund_id": int(time.time()),
        "amount": float(refund_in.refund_amount),
        "reason": refund_in.reason,
        "refunded_by": current_user.user_id,
        "refunded_at": datetime.now(timezone(timedelta(hours=7))).isoformat()
    }
    previous_refunds.append(refund_record)
    
    refund_note = f"\n[Refunded: {refund_in.refund_amount}] Reason: {refund_in.reason}"
    notes = (transaction.notes or "") + refund_note

    await payment_crud.update(
        db=db,
        db_obj=transaction,
        obj_in={
            "status": new_payment_status,
            "notes": notes,
            "payment_metadata": {
                **payment_metadata,
                "refunds": previous_refunds,
                "total_refunded": float(current_total_refunded),
                "is_partially_refunded": not is_full_refund
            }
        }
    )
    

    order = await order_crud.get(db=db, id=transaction.order_id)
    if order:
        if is_full_refund:
            await order_crud.update_status(
                db=db,
                order_id=order.order_id,
                new_status=OrderStatusEnum.REFUNDED,
                note=f"Hoàn tiền toàn bộ: {refund_in.reason}",
                user_id=current_user.user_id
            )
            await order_crud.update(
                db=db, 
                db_obj=order, 
                obj_in={"payment_status": PaymentStatusEnum.REFUNDED}
            )
        else:
            update_data = {
                "payment_status": PaymentStatusEnum.PARTIAL_REFUNDED,
                "order_status": OrderStatusEnum.PARTIAL_REFUNDED
            }
            await order_crud.update(db=db, db_obj=order, obj_in=update_data)
   

    await create_audit_log(
        db=db, 
        user_id=current_user.user_id, 
        action="refund_transaction", 
        resource_type="payment_transaction", 
        resource_id=refund_in.transaction_id,
        details={"amount": float(refund_in.refund_amount), "status": new_payment_status}
    )
    
    background_tasks.add_task(
        invalidate_caches_task,
        user_id=order.user_id if order else None,
        order_id=order.order_id if order else None,
        transaction_id=refund_in.transaction_id,
        clear_admin=True, 
        clear_stats=True
    )
    
    return RefundResponse(
        refund_id=refund_record["refund_id"],
        transaction_id=refund_in.transaction_id,
        refund_amount=refund_in.refund_amount,
        status="completed" if is_full_refund else "partial",
        created_at=datetime.now(timezone(timedelta(hours=7)))
    )

@router.post("/webhooks/payos")
async def payos_webhook_handler(
    *,
    db: SessionDep,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Xử lý thông báo tự động (Webhook) từ cổng thanh toán PayOS để cập nhật trạng thái đơn hàng theo thời gian thực.
    """
    payos = PayOSService()
    
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body"
        )
    
    status_code = body.get("code")
    desc = body.get("desc")
    webhook_data = body.get("data", {})
    signature = body.get("signature") 
    if not signature:
         signature = request.headers.get("x-signature", "")

    logger.info(f"Webhook PayOS received. Code: {status_code}, Desc: {desc}")
    
    is_valid = payos.verify_webhook_signature(webhook_data, signature)
    
    if not is_valid:
        logger.warning(f"Invalid signature. Desc: {desc}")
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
        if (datetime.now(timezone(timedelta(hours=7))) - lock_time).seconds < settings.PAYMENT_WEBHOOK_LOCK_TIMEOUT:
            logger.info(f"Webhook already being processed: {lock_key}")
            return {"message": "Already processing", "processed": False}
    
    _webhook_locks[lock_key] = datetime.now(timezone(timedelta(hours=7)))
    
    try:
        transaction = await payment_crud.get_by_gateway_transaction_id(
            db=db,
            gateway_transaction_id=payos_order_code
        )
        
        if not transaction:
            logger.warning(f"Transaction not found for PayOS order: {payos_order_code}")
            return {"message": "Transaction not found", "processed": False}
        
        order = await order_crud.get_with_details(db=db, id=transaction.order_id)
        if not order:
            logger.error(f"Order not found for transaction: {transaction.transaction_id}")
            return {"message": "Order not found", "processed": False}
        
        if status_code == "00":
            if transaction.status == PaymentStatusEnum.PAID and transaction.gateway_transaction_id == reference:
                logger.info(f"Transaction already marked as paid: {transaction.transaction_id}")
                return {
                    "message": "Already processed",
                    "processed": True,
                    "order_id": order.order_id
                }
            
            update_data = {
                "status": PaymentStatusEnum.PAID,
                "gateway_transaction_id": reference,
                "notes": "Payment completed successfully via PayOS webhook",
                "gateway_response": json.dumps(webhook_data),
                "payment_metadata": {
                    **(transaction.payment_metadata or {}),
                    "counter_account_name": webhook_data.get("counterAccountName"),
                    "counter_account_number": webhook_data.get("counterAccountNumber"),
                    "transaction_datetime": transaction_datetime,
                    "webhook_processed_at": datetime.now(timezone(timedelta(hours=7))).isoformat()
                }
            }

            if order:
                purchased_variant_ids = [item.variant_id for item in order.items]
                await cart_crud.remove_items_after_checkout(
                    db=db,
                    user_id=order.user_id,
                    variant_ids=purchased_variant_ids
                )

            if not transaction.paid_at:
                update_data["paid_at"] = datetime.now(timezone(timedelta(hours=7)))

            
            if order.order_status == OrderStatusEnum.CANCELLED:
                logger.warning(f"Payment received for CANCELLED order. OrderID: {order.order_id}, TxnID: {transaction.transaction_id}")
                
                update_data["notes"] = "WARNING: Payment received AFTER order was CANCELLED. Manual refund required."

                await payment_crud.update(
                    db=db,
                    db_obj=transaction,
                    obj_in=update_data
                )
                return {
                    "message": "Payment received for cancelled order",
                    "processed": True,
                    "order_id": order.order_id,
                    "warning": "Order was already cancelled"
                }
            
            await payment_crud.update(
                db=db,
                db_obj=transaction,
                obj_in=update_data
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
                    "payment_metadata": {
                        **(transaction.payment_metadata or {}),
                        "failure_code": status_code,
                        "webhook_processed_at": datetime.now(timezone(timedelta(hours=7))).isoformat()
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
    """
    Kiểm tra tình trạng sức khỏe của hệ thống thanh toán, bao gồm kết nối Database và trạng thái hoạt động của cổng PayOS.
    """
    health_status = {
        "status": "online",
        "timestamp": datetime.now(timezone(timedelta(hours=7))).isoformat()
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
        is_config_ready = settings.PAYOS_ENABLED

        is_db_active = await system_setting.get_value(
            db=db, 
            key="payment_method_payos_enabled", 
            default=True
        )

        health_status["payos"] = {
            "configured": is_config_ready,
            "active_mode": is_db_active,
            "final_status": "ready" if (is_config_ready and is_db_active) else "disabled"
        }
    except Exception as e:
        health_status["payos"] = {"error": str(e)}
    
    if health_status.get("database") != "healthy":
        health_status["status"] = "degraded"
    
    return health_status