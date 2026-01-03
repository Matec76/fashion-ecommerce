from typing import List

from fastapi import APIRouter, Query, status, HTTPException, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    require_permission,
)
from app.crud.inventory import inventory_transaction as transaction_crud
from app.crud.inventory import variant_stock as stock_crud
from app.crud.inventory import stock_alert as alert_crud
from app.models.inventory import (
    InventoryTransactionResponse,
    InventoryTransactionCreate,
    InventoryBulkAdjust,
    InventoryTransfer,
    VariantStockResponse,
    VariantStockSummary,
    VariantStockUpdate,
    StockAlertResponse,
)
from app.models.common import Message
from app.models.enums import InventoryChangeEnum
from app.models.user import User

router = APIRouter()


@router.get("/transactions", response_model=List[InventoryTransactionResponse])
@cache(expire=300, namespace="inventory")
async def get_inventory_transactions(
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.view")),
    variant_id: int | None = Query(None, description="Filter by variant"),
    warehouse_id: int | None = Query(None, description="Filter by warehouse"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[InventoryTransactionResponse]:
    """
    Lấy danh sách các giao dịch biến động kho (Dành cho Admin).
    """
    if variant_id:
        transactions = await transaction_crud.get_by_variant(
            db=db,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            skip=skip,
            limit=limit
        )
    elif warehouse_id:
        transactions = await transaction_crud.get_by_warehouse(
            db=db,
            warehouse_id=warehouse_id,
            skip=skip,
            limit=limit
        )
    else:
        transactions = await transaction_crud.get_multi(
            db=db,
            skip=skip,
            limit=limit
        )
    
    return [
        InventoryTransactionResponse(
            transaction_id=t.transaction_id,
            variant_id=t.variant_id,
            warehouse_id=t.warehouse_id,
            transaction_type=t.transaction_type,
            quantity=t.quantity,
            balance_after=t.balance_after,
            reference=t.reference,
            note=t.note,
            performed_by=t.performed_by,
            created_at=t.created_at,
            variant_summary={
                "variant_id": t.variant.variant_id,
                "sku": t.variant.sku,
            } if t.variant else None,
            warehouse_summary={
                "warehouse_id": t.warehouse.warehouse_id,
                "warehouse_name": t.warehouse.warehouse_name,
            } if t.warehouse else None,
            user_summary={
                "user_id": t.user.user_id,
                "full_name": f"{t.user.first_name} {t.user.last_name}" if t.user.first_name else t.user.email,
            } if t.user else None
        )
        for t in transactions
    ]


@router.post("/adjust", response_model=InventoryTransactionResponse, status_code=status.HTTP_201_CREATED)
async def adjust_inventory(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.update")),
    transaction_in: InventoryTransactionCreate,
) -> InventoryTransactionResponse:
    """
    Điều chỉnh số lượng tồn kho của một biến thể (Dành cho Admin).
    """
    try:
        transaction = await transaction_crud.create_transaction(
            db=db,
            variant_id=transaction_in.variant_id,
            warehouse_id=transaction_in.warehouse_id,
            transaction_type=transaction_in.transaction_type,
            quantity=transaction_in.quantity,
            performed_by=current_user.user_id,
            reference=transaction_in.reference,
            note=transaction_in.note
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    await FastAPICache.clear(namespace="inventory")
    
    return InventoryTransactionResponse(
        transaction_id=transaction.transaction_id,
        variant_id=transaction.variant_id,
        warehouse_id=transaction.warehouse_id,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        balance_after=transaction.balance_after,
        reference=transaction.reference,
        note=transaction.note,
        performed_by=transaction.performed_by,
        created_at=transaction.created_at
    )


@router.post("/bulk-adjust", response_model=Message, status_code=status.HTTP_201_CREATED)
async def bulk_adjust_inventory(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.update")),
    bulk_in: InventoryBulkAdjust,
) -> Message:
    """
    Thực hiện điều chỉnh tồn kho cho nhiều biến thể cùng lúc (Dành cho Admin).
    """
    count = 0
    errors = []
    
    for adjustment in bulk_in.adjustments:
        try:
            await transaction_crud.create_transaction(
                db=db,
                variant_id=adjustment["variant_id"],
                warehouse_id=bulk_in.warehouse_id,
                transaction_type=bulk_in.transaction_type,
                quantity=adjustment["quantity"],
                performed_by=current_user.user_id,
                reference=bulk_in.reference,
                note=adjustment.get("note")
            )
            count += 1
        except Exception as e:
            errors.append(f"Variant {adjustment['variant_id']}: {str(e)}")
    
    await FastAPICache.clear(namespace="inventory")
    
    if errors:
        return Message(
            message=f"{count} adjustments successful, {len(errors)} failed. Errors: {', '.join(errors)}"
        )
    
    return Message(message=f"{count} inventory adjustments completed successfully")


@router.post("/transfer", response_model=Message, status_code=status.HTTP_201_CREATED)
async def transfer_inventory(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.update")),
    transfer_in: InventoryTransfer,
) -> Message:
    """
    Điều chuyển hàng hóa giữa các kho hàng khác nhau (Dành cho Admin).
    """
    if transfer_in.from_warehouse_id == transfer_in.to_warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to the same warehouse"
        )
    
    source_stock = await stock_crud.get_by_variant_warehouse(
        db=db,
        variant_id=transfer_in.variant_id,
        warehouse_id=transfer_in.from_warehouse_id
    )
    
    if not source_stock or source_stock.available < transfer_in.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock in source warehouse. Available: {source_stock.available if source_stock else 0}"
        )
    
    try:
        await transaction_crud.create_transaction(
            db=db,
            variant_id=transfer_in.variant_id,
            warehouse_id=transfer_in.from_warehouse_id,
            transaction_type=InventoryChangeEnum.TRANSFER_OUT,
            quantity=-transfer_in.quantity,
            performed_by=current_user.user_id,
            reference=transfer_in.reference,
            note=f"Transfer to warehouse {transfer_in.to_warehouse_id}: {transfer_in.note or ''}"
        )
        
        await transaction_crud.create_transaction(
            db=db,
            variant_id=transfer_in.variant_id,
            warehouse_id=transfer_in.to_warehouse_id,
            transaction_type=InventoryChangeEnum.TRANSFER_IN,
            quantity=transfer_in.quantity,
            performed_by=current_user.user_id,
            reference=transfer_in.reference,
            note=f"Transfer from warehouse {transfer_in.from_warehouse_id}: {transfer_in.note or ''}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    await FastAPICache.clear(namespace="inventory")
    
    return Message(message=f"Successfully transferred {transfer_in.quantity} units")


@router.get("/stock/variant/{variant_id}", response_model=VariantStockSummary)
@cache(expire=10, namespace="inventory")
async def get_variant_stock(
    db: SessionDep,
    variant_id: int,
    current_user: User = Depends(require_permission("inventory.view")),
) -> VariantStockSummary:
    """
    Lấy thông tin tóm tắt số lượng tồn kho của một biến thể trên toàn bộ hệ thống kho.
    """
    stocks = await stock_crud.get_by_variant(db=db, variant_id=variant_id)
    
    if not stocks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No stock found for this variant"
        )
    
    total_summary = await stock_crud.get_total_stock(db=db, variant_id=variant_id)
    
    warehouses_data = [
        {
            "warehouse_id": s.warehouse.warehouse_id,
            "warehouse_name": s.warehouse.warehouse_name,
            "quantity": s.quantity,
            "reserved": s.reserved,
            "available": s.available
        }
        for s in stocks if s.warehouse
    ]
    
    return VariantStockSummary(
        variant_id=variant_id,
        total_quantity=total_summary["total_quantity"],
        total_reserved=total_summary["total_reserved"],
        total_available=total_summary["total_available"],
        warehouses=warehouses_data
    )


@router.post("/stock/reserve", response_model=VariantStockResponse)
async def reserve_stock(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.view")),
    variant_id: int = Query(...),
    warehouse_id: int = Query(...),
    quantity: int = Query(..., gt=0),
) -> VariantStockResponse:
    """
    Thực hiện giữ chỗ (tạm khóa) số lượng tồn kho để phục vụ việc tạo đơn hàng.
    """
    try:
        stock = await stock_crud.reserve_stock(
            db=db,
            variant_id=variant_id,
            warehouse_id=warehouse_id,
            quantity=quantity
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    await FastAPICache.clear(namespace="inventory")
    
    return VariantStockResponse(
        stock_id=stock.stock_id,
        variant_id=stock.variant_id,
        warehouse_id=stock.warehouse_id,
        quantity=stock.quantity,
        reserved=stock.reserved,
        available=stock.available,
        created_at=stock.created_at,
        updated_at=stock.updated_at
    )


@router.post("/stock/release", response_model=VariantStockResponse)
async def release_stock(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.view")),
    variant_id: int = Query(...),
    warehouse_id: int = Query(...),
    quantity: int = Query(..., gt=0),
) -> VariantStockResponse:
    """
    Giải phóng số lượng tồn kho đã được giữ chỗ trước đó.
    """
    stock = await stock_crud.release_stock(
        db=db,
        variant_id=variant_id,
        warehouse_id=warehouse_id,
        quantity=quantity
    )
    
    await FastAPICache.clear(namespace="inventory")
    
    return VariantStockResponse(
        stock_id=stock.stock_id,
        variant_id=stock.variant_id,
        warehouse_id=stock.warehouse_id,
        quantity=stock.quantity,
        reserved=stock.reserved,
        available=stock.available,
        created_at=stock.created_at,
        updated_at=stock.updated_at
    )


@router.patch("/stock/{stock_id}", response_model=VariantStockResponse)
async def update_stock(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.update")),
    stock_id: int,
    stock_in: VariantStockUpdate,
) -> VariantStockResponse:
    """
    Cập nhật trực tiếp số liệu bản ghi tồn kho (Dành cho Admin).
    """
    stock = await stock_crud.get(db=db, id=stock_id)
    
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock record not found"
        )
    
    updated_stock = await stock_crud.update(
        db=db,
        db_obj=stock,
        obj_in=stock_in
    )
    
    await FastAPICache.clear(namespace="inventory")
    
    return VariantStockResponse(
        stock_id=updated_stock.stock_id,
        variant_id=updated_stock.variant_id,
        warehouse_id=updated_stock.warehouse_id,
        quantity=updated_stock.quantity,
        reserved=updated_stock.reserved,
        available=updated_stock.available,
        created_at=updated_stock.created_at,
        updated_at=updated_stock.updated_at
    )


@router.get("/alerts", response_model=List[StockAlertResponse])
@cache(expire=60, namespace="inventory")
async def get_stock_alerts(
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.view")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[StockAlertResponse]:
    """
    Lấy danh sách các cảnh báo tồn kho chưa được xử lý (Dành cho Admin).
    """
    alerts = await alert_crud.get_unresolved(
        db=db,
        skip=skip,
        limit=limit
    )
    
    return [
        StockAlertResponse(
            alert_id=a.alert_id,
            variant_id=a.variant_id,
            alert_type=a.alert_type,
            threshold=a.threshold,
            current_stock=a.current_stock,
            is_resolved=a.is_resolved,
            resolved_at=a.resolved_at,
            resolved_by=a.resolved_by,
            notified_at=a.notified_at,
            notification_sent=a.notification_sent,
            created_at=a.created_at,
            variant_summary={
                "variant_id": a.variant.variant_id,
                "sku": a.variant.sku,
                "product_name": a.variant.product.product_name if a.variant and a.variant.product else None,
            } if a.variant else None
        )
        for a in alerts
    ]


@router.post("/alerts/{alert_id}/resolve", response_model=StockAlertResponse)
async def resolve_stock_alert(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.update")),
    alert_id: int,
) -> StockAlertResponse:
    """
    Xác nhận đã xử lý một cảnh báo tồn kho cụ thể (Dành cho Admin).
    """
    try:
        alert = await alert_crud.resolve_alert(
            db=db,
            alert_id=alert_id,
            resolved_by=current_user.user_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    await FastAPICache.clear(namespace="inventory")
    
    return StockAlertResponse(
        alert_id=alert.alert_id,
        variant_id=alert.variant_id,
        alert_type=alert.alert_type,
        threshold=alert.threshold,
        current_stock=alert.current_stock,
        is_resolved=alert.is_resolved,
        resolved_at=alert.resolved_at,
        resolved_by=alert.resolved_by,
        notified_at=alert.notified_at,
        notification_sent=alert.notification_sent,
        created_at=alert.created_at,
        variant_summary={
            "variant_id": alert.variant.variant_id,
            "sku": alert.variant.sku,
            "product_name": alert.variant.product.product_name if alert.variant and alert.variant.product else None,
        } if alert.variant else None
    )