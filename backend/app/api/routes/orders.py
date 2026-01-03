from typing import Any, Optional
from datetime import datetime, timedelta, timezone
import time
import json

from fastapi import APIRouter, Body, Query, Request, status, HTTPException, BackgroundTasks, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update

from app.api.deps import (
    SessionDep,
    CurrentUser,
    PaginationDep,
    require_permission,
    _get_user_permissions,
)
from app.crud.order import order as order_crud
from app.crud.order import order_status_history as status_history_crud
from app.crud.order import shipping_method as shipping_crud
from app.crud.cart import cart as cart_crud, cart_item as cart_item_crud
from app.crud.payment import payment_transaction as payment_crud
from app.crud.payment_method import payment_method as payment_method_crud
from app.models.product import ProductVariant
from app.models.order import (
    Order,
    OrderResponse,
    OrderDetailResponse,
    OrderCreate,
    OrderUpdate,
    OrderStatusUpdate,
    ShippingMethodResponse,
    ShippingMethodCreate,
    ShippingMethodUpdate,
    OrderStatistics,
    OrderCreationResponse,
)
from app.models.payment import PaymentTransactionCreate, PaymentResponseInfo
from app.models.enums import PaymentStatusEnum, PaymentMethodType, OrderStatusEnum
from app.models.common import Message
from app.services.payos_service import PayOSService
from app.core.config import settings
from app.models.user import User
from app.models.coupon import Coupon, OrderCoupon
from app.crud.system import system_setting

router = APIRouter()


def extract_client_ip(request: Request) -> str:
    """
    Trích xuất địa chỉ IP của khách hàng từ tiêu đề yêu cầu HTTP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    if request.client:
        return request.client.host
    
    return "unknown"


def extract_user_agent(request: Request) -> str:
    """
    Trích xuất thông tin thiết bị (User-Agent) của khách hàng.
    """
    user_agent = request.headers.get("User-Agent", "unknown")
    
    max_length = 255
    if len(user_agent) > max_length:
        user_agent = user_agent[:max_length]
    
    return user_agent


async def invalidate_order_caches(user_id: int, order_id: Optional[int] = None):
    """
    Xóa toàn bộ các cụm cache liên quan khi dữ liệu đơn hàng thay đổi.
    """
    cache_namespaces = [
        "orders:user:list",
        "orders:admin:list",
        "order:detail",
        "order:detail:admin",
        "order:by_number",
        "order:history",
        "orders:stats:overview",
    ]
    
    for ns in cache_namespaces:
        try:
            await FastAPICache.clear(namespace=ns)
        except Exception as e:
            print(f"Cache invalidation error for namespace {ns}: {e}")


def extract_user_id(user_obj: Any) -> Optional[int]:
    """Extract user_id from User object or return None"""
    if user_obj is None:
        return None
    return user_obj.user_id if hasattr(user_obj, "user_id") else user_obj


def extract_pagination_params(pagination: Any) -> tuple[int, int]:
    """Extract skip and limit from pagination object"""
    if pagination is None:
        return 0, 100
    return pagination.get_offset(), pagination.get_limit()


def make_cache_key_builder(prefix: str):
    def key_builder(func, namespace: str = "", request: Request = None, *args, **kwargs):
        user_obj = kwargs.get("current_user")
        user_id = user_obj.user_id if hasattr(user_obj, "user_id") else "guest"
        
        pagination = kwargs.get("pagination")
        skip = pagination.get_offset() if pagination else 0
        limit = pagination.get_limit() if pagination else 100
        
        status_filter = kwargs.get("status", "all")
        search = kwargs.get("search", "none")
        
        return f"{namespace}:{prefix}:u:{user_id}:s:{status_filter}:p:{skip}:{limit}:q:{search}"
    return key_builder


async def initiate_payment_transaction(
    *,
    db: SessionDep,
    order: Any,
    payment_method_code: str,
    request: Request,
) -> PaymentResponseInfo:
  
    existing_pending = await payment_crud.get_duplicate_transactions(
        db=db,
        order_id=order.order_id,
        amount=order.total_amount,
        gateway=payment_method_code,
        minutes=15
    )
    
    if existing_pending:
        latest_txn = existing_pending[0]
        if latest_txn.payment_url:
            return PaymentResponseInfo(
                payment_method=payment_method_code,
                transaction_id=latest_txn.transaction_id,
                message="Thanh toán giao dịch",
                payment_url=latest_txn.payment_url,
                qr_code=latest_txn.qr_code
            )

    timestamp_str = str(int(time.time()))
    unique_txn_code = f"{order.order_number}_{timestamp_str}"
    payos_order_code = int(f"{order.order_id}{int(time.time()) % 1000000}")

    transaction_create = PaymentTransactionCreate(
        order_id=order.order_id,
        payment_method_id=order.payment_method_id,
        amount=order.total_amount,
        status=PaymentStatusEnum.PENDING,
        payment_gateway=payment_method_code,
        transaction_code=unique_txn_code,
        gateway_transaction_id=str(payos_order_code),
        payment_metadata={
            "payos_order_code": str(payos_order_code)
        }
    )
    
    transaction = await payment_crud.create(db=db, obj_in=transaction_create)

    try:
        if payment_method_code == PaymentMethodType.BANK_TRANSFER.value:
            
            if not settings.PAYOS_ENABLED:
                raise HTTPException(status_code=503, detail="Cổng thanh toán PayOS đang bảo trì (System Config)")

            is_payos_active = await system_setting.get_value(
                db=db, 
                key="payment_method_payos_enabled", 
                default=True
            )
            
            if not is_payos_active:
                await payment_crud.update(
                    db=db, 
                    db_obj=transaction, 
                    obj_in={"status": PaymentStatusEnum.FAILED, "notes": "Admin disabled PayOS via Settings"}
                )
                raise HTTPException(
                    status_code=503, 
                    detail="Cổng thanh toán PayOS đang tạm ngừng phục vụ. Vui lòng chọn phương thức khác."
                )

            payos_service = PayOSService()

            user_info = order.user_snapshot or {}
            buyer_name = f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
            if not buyer_name:
                buyer_name = "Guest Customer"

            payment_link_data = await payos_service.create_payment_link(
                order_id=order.order_id,
                order_code=payos_order_code,
                amount=int(order.total_amount),
                description=str(order.order_number),
                buyer_name=buyer_name,
                buyer_email=user_info.get('email', 'customer@example.com'),
                buyer_phone=user_info.get('phone_number', ''),
                cancel_url=f"{settings.FRONTEND_HOST}payment/payos/cancel",
                return_url=f"{settings.FRONTEND_HOST}payment/payos/return"
            )
            
            checkout_url = payment_link_data.get("checkoutUrl") 
            qr_code = payment_link_data.get("qrCode")
            
            await payment_crud.update(
                db=db,
                db_obj=transaction,
                obj_in={
                    "payment_url": checkout_url,
                    "qr_code": qr_code
                }
            )
            
            return PaymentResponseInfo(
                payment_method=payment_method_code,
                transaction_id=transaction.transaction_id,
                message="Vui lòng quét mã QR để thanh toán", 
                payment_url=checkout_url,
                qr_code=qr_code
            )

        elif payment_method_code == PaymentMethodType.COD.value:
            is_cod_active = await system_setting.get_value(
                db=db, 
                key="payment_method_cod_enabled", 
                default=True
            )
            
            if not is_cod_active:
                await payment_crud.update(
                    db=db, 
                    db_obj=transaction, 
                    obj_in={"status": PaymentStatusEnum.FAILED, "notes": "Admin disabled COD"}
                )
                raise HTTPException(
                    status_code=503, 
                    detail="Thanh toán khi nhận hàng (COD) đang tạm khóa. Vui lòng chọn phương thức khác."
                )
            
            return PaymentResponseInfo(
                payment_method=payment_method_code,
                transaction_id=transaction.transaction_id,
                message="Vui lòng thanh toán khi nhận hàng",
                payment_url=None,
                qr_code=None
            )
            
        else:
            raise HTTPException(status_code=400, detail="Phương thức thanh toán không được hỗ trợ")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        await payment_crud.update(
            db=db, 
            db_obj=transaction, 
            obj_in={"status": PaymentStatusEnum.FAILED}
        )
    
        print(f"Lỗi khởi tạo thanh toán PayOS: {str(e)}")
        
        raise HTTPException(
            status_code=502, 
            detail="Lỗi kết nối cổng thanh toán. Vui lòng thử lại."
        )


@router.post("", response_model=OrderCreationResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    order_in: OrderCreate,
    request: Request,
    background_tasks: BackgroundTasks,
) -> OrderCreationResponse:
    """
    Tạo một đơn hàng mới từ giỏ hàng hiện tại của người dùng.
    """
    cart = await cart_crud.get_by_user(db=db, user_id=current_user.user_id)
    
    if not cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")
    
    order_ip = extract_client_ip(request)
    order_device = extract_user_agent(request)

    try:
        order = await order_crud.create_from_cart(
            db=db,
            cart_id=cart.cart_id,
            user_id=current_user.user_id,
            shipping_address_id=order_in.shipping_address_id,
            billing_address_id=order_in.billing_address_id or order_in.shipping_address_id,
            shipping_method_id=order_in.shipping_method_id,
            payment_method_id=order_in.payment_method_id,
            notes=order_in.notes,
            coupon_code=order_in.coupon_code,
            order_ip=order_ip,
            order_device=order_device,
            commit=False
        )
        
        payment_method = await payment_method_crud.get(db=db, id=order_in.payment_method_id)
        if not payment_method:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment method")
        
        if payment_method.method_code == PaymentMethodType.COD.value:
            cart_items = await cart_item_crud.get_by_cart(db=db, cart_id=cart.cart_id)
            
            if cart_items:
                purchased_variant_ids = [item.variant_id for item in cart_items]

                await cart_crud.remove_items_after_checkout(
                    db=db,
                    user_id=current_user.user_id,
                    variant_ids=purchased_variant_ids
                )
        
        payment_response = await initiate_payment_transaction(
            db=db,
            order=order,
            payment_method_code=payment_method.method_code,
            request=request,
        )
        
        await db.commit()
        await db.refresh(order)
        
        order_detail = await order_crud.get_with_details(db=db, id=order.order_id)

        if order_detail and order_detail.items:
            prefix = FastAPICache.get_prefix() or ""
            unique_product_ids = {item.variant.product_id for item in order_detail.items if item.variant}
            
            for pid in unique_product_ids:
                await FastAPICache.clear(key=f"{prefix}:product:variants:{pid}")
                await FastAPICache.clear(key=f"{prefix}:product:detail:{pid}")
        
        background_tasks.add_task(
            invalidate_order_caches,
            user_id=current_user.user_id,
            order_id=order.order_id
        )
        
        return OrderCreationResponse(
            order=order_detail,
            payment=payment_response
        )
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create order: {str(e)}"
        )


@router.post("/{order_id}/pay", response_model=PaymentResponseInfo)
async def repay_order(
    *,
    db: SessionDep,
    order_id: int,
    current_user: CurrentUser,
    payment_method_id: int,
    request: Request
) -> PaymentResponseInfo:
    """
    Thanh toán lại nếu bị lỗi.
    """
    order = await order_crud.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
    
    if order.user_id != current_user.user_id:
        user_perms = await _get_user_permissions(db, current_user)
        if "*" not in user_perms and "order.update" not in user_perms:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập đơn hàng này")

    if order.order_status != OrderStatusEnum.PENDING:
         raise HTTPException(status_code=400, detail="Đơn hàng không ở trạng thái chờ thanh toán")

    payment_method = await payment_method_crud.get(db=db, id=payment_method_id)
    if not payment_method:
        raise HTTPException(status_code=404, detail="Phương thức thanh toán không tồn tại")
    
    if order.payment_method_id != payment_method_id:
        order = await order_crud.update(
            db=db, 
            db_obj=order, 
            obj_in={"payment_method_id": payment_method_id}
        )

    return await initiate_payment_transaction(
        db=db,
        order=order,
        payment_method_code=payment_method.method_code, 
        request=request
    )

@router.get("/payment/payos/return")
async def payos_return_handler(
    *,
    db: SessionDep,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Xử lý Return URL an toàn: Gọi PayOS kiểm tra trạng thái thực tế.
    """
    query_params = dict(request.query_params)
    payos_order_code = query_params.get("orderCode")
    
    if not payos_order_code:
        raise HTTPException(status_code=400, detail="Missing order code")

    transaction = await payment_crud.get_by_gateway_transaction_id(
        db=db, 
        gateway_transaction_id=str(payos_order_code)
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    order = await order_crud.get_with_details(db=db, id=transaction.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    payos_service = PayOSService()
    try:
        payment_info = await payos_service.check_payment_status(str(payos_order_code))
        real_status = payment_info.get("status")
    except Exception as e:
        print(f"Verify PayOS failed: {e}")
        return {"success": False, "message": "Verification failed"}

    if real_status == "PAID":
        if transaction.status != PaymentStatusEnum.PAID:

            purchased_variant_ids = [item.variant_id for item in order.items]
            await cart_crud.remove_items_after_checkout(
                db=db, 
                user_id=order.user_id, 
                variant_ids=purchased_variant_ids
            )

            await payment_crud.update(
                db=db,
                db_obj=transaction,
                obj_in={
                    "status": PaymentStatusEnum.PAID,
                    "paid_at": datetime.now(timezone(timedelta(hours=7))),
                    "notes": "Payment verified via PayOS Return Check",
                    "gateway_response": json.dumps(payment_info)
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
            
            background_tasks.add_task(invalidate_order_caches, user_id=order.user_id, order_id=order.order_id)
        
        return {
            "success": True,
            "message": "Payment verified and successful",
            "order_number": order.order_number
        }
    
    elif query_params.get("cancel") == "true":
        if transaction.status != PaymentStatusEnum.PAID:
            
            await payment_crud.update(
                db=db,
                db_obj=transaction,
                obj_in={
                    "status": PaymentStatusEnum.CANCELLED,
                    "notes": "User cancelled payment at PayOS gateway"
                }
            )

            if order.order_status != OrderStatusEnum.CANCELLED:
                await order_crud.update_status(
                    db=db,
                    order_id=order.order_id,
                    new_status=OrderStatusEnum.CANCELLED,
                    comment="Khách hàng hủy thanh toán tại cổng PayOS",
                    updated_by=order.user_id
                )
                
                await order_crud.update(
                    db=db,
                    db_obj=order,
                    obj_in={"payment_status": PaymentStatusEnum.FAILED}
                )

        return {"success": False, "message": "Payment cancelled"}


@router.post("/{order_id}/payment/confirm-cod", response_model=OrderResponse)
async def confirm_cod_payment(
    *,
    db: SessionDep,
    order_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("order.update")),
) -> OrderResponse:
    """
    Xác nhận đã nhận tiền mặt cho đơn hàng COD (Dành cho Admin).
    """
    order = await order_crud.get(db=db, id=order_id)
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    payment_method = await payment_method_crud.get(db=db, id=order.payment_method_id)
    if payment_method.method_code != PaymentMethodType.COD.value:
        raise HTTPException(status_code=400, detail="This order does not use COD payment method")
    
    transactions = await payment_crud.get_by_order(db=db, order_id=order_id)
    if transactions:
        transaction = transactions[0]
        await payment_crud.update(
            db=db,
            db_obj=transaction,
            obj_in={
                "status": PaymentStatusEnum.PAID,
                "paid_at": datetime.now(timezone(timedelta(hours=7))),
                "notes": f"COD payment confirmed by admin (User ID: {current_user.user_id})"
            }
        )
    
    updated_order = await order_crud.update(
        db=db,
        db_obj=order,
        obj_in={"payment_status": PaymentStatusEnum.PAID}
    )
    
    background_tasks.add_task(invalidate_order_caches, user_id=order.user_id, order_id=order.order_id)
    return updated_order


@router.get("/me", response_model=list[OrderResponse])
@cache(
    expire=300,
    namespace="orders:user:list",
    key_builder=make_cache_key_builder("me")
)
async def get_my_orders(
    db: SessionDep,
    current_user: CurrentUser,
    pagination: PaginationDep,
    status: OrderStatusEnum | None = Query(None, description="Filter by status"),
) -> list[OrderResponse]:
    """
    Lấy danh sách các đơn hàng của người dùng hiện tại (Có phân trang và lọc theo trạng thái).
    """
    orders = await order_crud.get_by_user(
        db=db,
        user_id=current_user.user_id,
        skip=pagination.get_offset(),
        limit=pagination.get_limit(),
        status=status
    )
    
    return orders


@router.get("/me/{order_id}", response_model=OrderDetailResponse)
@cache(
    expire=180,
    namespace="order:detail",
    key_builder=make_cache_key_builder("detail")
)
async def get_my_order(
    db: SessionDep,
    current_user: CurrentUser,
    order_id: int,
) -> OrderDetailResponse:
    """
    Xem thông tin chi tiết của một đơn hàng cụ thể thuộc người dùng hiện tại.
    """
    order = await order_crud.get_with_details(db=db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    return order


@router.post("/me/{order_id}/cancel", response_model=OrderResponse)
async def cancel_my_order(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    order_id: int,
    background_tasks: BackgroundTasks,
    is_user_cancel: bool = Body(True, embed=True), 
) -> OrderResponse:
    """
    Hủy đơn hàng nếu người dùng là true, do hệ thống là false
    """
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.order_coupons).selectinload(OrderCoupon.coupon)
        )
        .where(Order.order_id == order_id)
        .with_for_update()
    )
    order = (await db.execute(stmt)).scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    allow_cancel_statuses = [OrderStatusEnum.PENDING, OrderStatusEnum.CONFIRMED, OrderStatusEnum.PROCESSING]
    if order.order_status not in allow_cancel_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Cannot cancel order with status {order.order_status.value}"
        )

    if is_user_cancel:
        reason_text = "Khách hàng chủ động hủy"
        
        if order.payment_status == PaymentStatusEnum.PAID:
            new_payment_status = PaymentStatusEnum.PAID 
            reason_text += " (Đã thanh toán - Chờ hoàn tiền)"
        else:
            new_payment_status = PaymentStatusEnum.CANCELLED
            
    else:
        reason_text = "Lỗi thanh toán hoặc Hết hạn (Auto-cancel)"
        new_payment_status = PaymentStatusEnum.FAILED

    updated_order = await order_crud.update_status(
        db=db,
        order_id=order_id,
        new_status=OrderStatusEnum.CANCELLED,
        note=reason_text,
        user_id=current_user.user_id
    )

    updated_order = await order_crud.update(
        db=db,
        db_obj=updated_order,
        obj_in={"payment_status": new_payment_status}
    )

    transactions = await payment_crud.get_by_order(db=db, order_id=order_id)
    for txn in transactions:
        if txn.status == PaymentStatusEnum.PENDING:
            await payment_crud.update(
                db=db, 
                db_obj=txn, 
                obj_in={
                    "status": PaymentStatusEnum.CANCELLED,
                    "notes": f"Cancelled: {reason_text}"
                }
            )
    
    await db.commit() 
    
    background_tasks.add_task(invalidate_order_caches, user_id=current_user.user_id, order_id=order_id)
    
    return updated_order


@router.get("", response_model=list[OrderResponse])
@cache(
    expire=120,
    namespace="orders:admin:list",
    key_builder=make_cache_key_builder("admin_list")
)
async def list_orders(
    db: SessionDep,
    pagination: PaginationDep,
    status: OrderStatusEnum | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by order number, user email, or phone"),
    current_user: User = Depends(require_permission("order.view")),
) -> list[OrderResponse]:
    """
    Liệt kê toàn bộ đơn hàng trên hệ thống (Dành cho Admin - Hỗ trợ tìm kiếm và lọc).
    """
    if search:
        orders = await order_crud.search(
            db=db,
            query=search,
            skip=pagination.get_offset(),
            limit=pagination.get_limit()
        )
    elif status:
        orders = await order_crud.get_by_status(
            db=db,
            status=status,
            skip=pagination.get_offset(),
            limit=pagination.get_limit()
        )
    else:
        orders = await order_crud.get_multi(
            db=db,
            skip=pagination.get_offset(),
            limit=pagination.get_limit(),
            order_by="created_at",
            order_desc=True
        )
    
    return orders


@router.get("/{order_id}", response_model=OrderDetailResponse)
@cache(
    expire=180,
    namespace="order:detail:admin",
    key_builder=make_cache_key_builder("admin_detail")
)
async def get_order(
    db: SessionDep,
    order_id: int,
    current_user: User = Depends(require_permission("order.view")),
) -> OrderDetailResponse:
    """
    Xem chi tiết hồ sơ đơn hàng bất kỳ theo ID (Dành cho Admin).
    """
    order = await order_crud.get_with_details(db=db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.get("/number/{order_number}", response_model=OrderDetailResponse)
@cache(
    expire=300,
    namespace="order:by_number",
    key_builder=make_cache_key_builder("by_number")
)
async def get_order_by_number(
    db: SessionDep,
    order_number: str,
    current_user: User = Depends(require_permission("order.view")),
) -> OrderDetailResponse:
    """
    Tìm kiếm thông tin đơn hàng thông qua Mã số đơn hàng (Dành cho Admin).
    """
    order = await order_crud.get_by_order_number(db=db, order_number=order_number)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    order_detail = await order_crud.get_with_details(db=db, id=order.order_id)
    
    return order_detail


@router.patch("/{order_id}", response_model=OrderResponse)
async def update_order(
    *,
    db: SessionDep,
    order_id: int,
    order_in: OrderUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("order.update")),
) -> OrderResponse:
    """
    Cập nhật thông tin chung của đơn hàng (Dành cho Admin).
    """
    order = await order_crud.get(db=db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    updated_order = await order_crud.update(
        db=db,
        db_obj=order,
        obj_in=order_in
    )
    
    background_tasks.add_task(
        invalidate_order_caches,
        user_id=order.user_id,
        order_id=order_id
    )
    
    return updated_order


@router.post("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    *,
    db: SessionDep,
    order_id: int,
    status_in: OrderStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("order.update")),
) -> OrderResponse:
    """
    Thay đổi trạng thái tiến trình của đơn hàng (Dành cho Admin).
    """
    order = await order_crud.get(db=db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    updated_order = await order_crud.update_status(
        db=db,
        order_id=order_id,
        new_status=status_in.order_status,
        comment=status_in.comment,
        updated_by=current_user.user_id
    )
    
    background_tasks.add_task(
        invalidate_order_caches,
        user_id=order.user_id,
        order_id=order_id
    )
    
    return updated_order


@router.get("/{order_id}/history", response_model=list)
@cache(
    expire=300,
    namespace="order:history",
    key_builder=make_cache_key_builder("history")
)
async def get_order_history(
    db: SessionDep,
    current_user: CurrentUser,
    order_id: int,
) -> list:
    """
    Xem lịch sử thay đổi trạng thái của một đơn hàng cụ thể.
    """
    order = await order_crud.get(db=db, id=order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.user_id != current_user.user_id:
        user_perms = await _get_user_permissions(db, current_user)
        if "*" not in user_perms and "order.view" not in user_perms:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this order"
            )
    
    history = await status_history_crud.get_by_order(db=db, order_id=order_id)
    
    return history


@router.get("/shipping-methods/all", response_model=list[ShippingMethodResponse])
@cache(
    expire=3600,
    namespace="shipping:methods:all"
)
async def list_shipping_methods(
    db: SessionDep,
) -> list[ShippingMethodResponse]:
    """
    Lấy danh sách các phương thức vận chuyển đang hoạt động.
    """
    methods = await shipping_crud.get_active(db=db)
    return methods


@router.post("/shipping-methods", response_model=ShippingMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_shipping_method(
    *,
    db: SessionDep,
    method_in: ShippingMethodCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("shipping.manage")),
) -> ShippingMethodResponse:
    """
    Tạo mới một phương thức vận chuyển (Dành cho Admin).
    """
    method = await shipping_crud.create(db=db, obj_in=method_in)
    
    background_tasks.add_task(
        FastAPICache.clear,
        namespace="shipping:methods:all"
    )
    
    return method


@router.patch("/shipping-methods/{method_id}", response_model=ShippingMethodResponse)
async def update_shipping_method(
    *,
    db: SessionDep,
    method_id: int,
    method_in: ShippingMethodUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("shipping.manage")),
) -> ShippingMethodResponse:
    """
    Cập nhật thông tin cấu hình của phương thức vận chuyển (Dành cho Admin).
    """
    method = await shipping_crud.get(db=db, id=method_id)
    
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipping method not found"
        )
    
    updated_method = await shipping_crud.update(
        db=db,
        db_obj=method,
        obj_in=method_in
    )
    
    background_tasks.add_task(
        FastAPICache.clear,
        namespace="shipping:methods:all"
    )
    
    return updated_method


@router.delete("/shipping-methods/{method_id}", response_model=Message)
async def delete_shipping_method(
    db: SessionDep,
    method_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("shipping.manage")),
) -> Message:
    """
    Xóa một phương thức vận chuyển khỏi hệ thống (Dành cho Admin).
    """
    method = await shipping_crud.get(db=db, id=method_id)
    
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipping method not found"
        )
    
    await shipping_crud.delete(db=db, id=method_id)
    
    background_tasks.add_task(
        FastAPICache.clear,
        namespace="shipping:methods:all"
    )
    
    return Message(message="Shipping method deleted successfully")


@router.get("/stats/overview", response_model=OrderStatistics)
@cache(
    expire=300,
    namespace="orders:stats:overview"
)
async def get_order_statistics(
    db: SessionDep,
    current_user: User = Depends(require_permission("analytics.view")),
) -> OrderStatistics:
    """
    Lấy các thông số thống kê tổng quát về tình hình đơn hàng và doanh thu trong 30 ngày qua (Dành cho Admin).
    """
    total_orders = await order_crud.count(db=db)
    pending_orders = await order_crud.count(db=db, filters={"order_status": OrderStatusEnum.PENDING})
    confirmed_orders = await order_crud.count(db=db, filters={"order_status": OrderStatusEnum.CONFIRMED})
    shipped_orders = await order_crud.count(db=db, filters={"order_status": OrderStatusEnum.SHIPPED})
    delivered_orders = await order_crud.count(db=db, filters={"order_status": OrderStatusEnum.DELIVERED})
    cancelled_orders = await order_crud.count(db=db, filters={"order_status": OrderStatusEnum.CANCELLED})
    
    start_date = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=30)
    end_date = datetime.now(timezone(timedelta(hours=7)))
    
    total_revenue = await order_crud.get_revenue_by_date_range(
        db=db,
        start_date=start_date,
        end_date=end_date
    )
    
    return OrderStatistics(
        total_orders=total_orders,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        total_revenue=total_revenue
    )