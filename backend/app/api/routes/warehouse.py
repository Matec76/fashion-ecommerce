from typing import List

from fastapi import APIRouter, Query, status, HTTPException, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    require_permission,
)
from app.crud.warehouse import warehouse as warehouse_crud
from app.models.warehouse import (
    WarehouseResponse,
    WarehouseDetailResponse,
    WarehouseCreate,
    WarehouseUpdate,
)
from app.models.common import Message
from app.models.user import User

router = APIRouter()


@router.get("", response_model=List[WarehouseResponse])
@cache(expire=600, namespace="warehouses")
async def list_warehouses(
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.view")),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[WarehouseResponse]:
    """
    Lấy danh sách các kho hàng đang hoạt động trên hệ thống.
    """
    warehouses = await warehouse_crud.get_active(
        db=db,
        skip=skip,
        limit=limit
    )
    
    return [
        WarehouseResponse(
            warehouse_id=w.warehouse_id,
            warehouse_name=w.warehouse_name,
            address=w.address,
            city=w.city,
            postal_code=w.postal_code,
            phone=w.phone,
            email=w.email,
            is_active=w.is_active,
            is_default=w.is_default,
            created_at=w.created_at,
            updated_at=w.updated_at
        )
        for w in warehouses
    ]


@router.get("/default", response_model=WarehouseResponse)
@cache(expire=600, namespace="warehouses")
async def get_default_warehouse(
    db: SessionDep,
    current_user: User = Depends(require_permission("inventory.view")),
) -> WarehouseResponse:
    """
    Truy vấn thông tin của kho hàng được thiết lập làm mặc định.
    """
    warehouse = await warehouse_crud.get_or_create_default(db=db)
    
    return WarehouseResponse(
        warehouse_id=warehouse.warehouse_id,
        warehouse_name=warehouse.warehouse_name,
        address=warehouse.address,
        city=warehouse.city,
        postal_code=warehouse.postal_code,
        phone=warehouse.phone,
        email=warehouse.email,
        is_active=warehouse.is_active,
        is_default=warehouse.is_default,
        created_at=warehouse.created_at,
        updated_at=warehouse.updated_at
    )


@router.get("/{warehouse_id}", response_model=WarehouseDetailResponse)
@cache(expire=300, namespace="warehouses")
async def get_warehouse(
    db: SessionDep,
    warehouse_id: int,
    current_user: User = Depends(require_permission("inventory.view")),
) -> WarehouseDetailResponse:
    """
    Xem thông tin chi tiết một kho hàng bao gồm cả tóm tắt tình trạng hàng hóa hiện có.
    """
    warehouse_data = await warehouse_crud.get_with_stock_summary(
        db=db,
        warehouse_id=warehouse_id
    )
    
    if not warehouse_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    warehouse = warehouse_data["warehouse"]
    
    return WarehouseDetailResponse(
        warehouse_id=warehouse.warehouse_id,
        warehouse_name=warehouse.warehouse_name,
        address=warehouse.address,
        city=warehouse.city,
        postal_code=warehouse.postal_code,
        phone=warehouse.phone,
        email=warehouse.email,
        is_active=warehouse.is_active,
        is_default=warehouse.is_default,
        created_at=warehouse.created_at,
        updated_at=warehouse.updated_at,
        total_variants=warehouse_data["total_variants"],
        total_quantity=warehouse_data["total_quantity"],
        total_reserved=warehouse_data["total_reserved"],
        total_available=warehouse_data["total_available"]
    )


@router.get("/{warehouse_id}/low-stock", response_model=List[dict])
@cache(expire=300, namespace="warehouses")
async def get_low_stock_variants(
    db: SessionDep,
    warehouse_id: int,
    threshold: int = Query(10, ge=0, le=100, description="Low stock threshold"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_permission("inventory.view")),
) -> List[dict]:
    """
    Lấy danh sách các sản phẩm có số lượng tồn kho dưới mức cảnh báo tại một kho cụ thể.
    """
    stocks = await warehouse_crud.get_low_stock_variants(
        db=db,
        warehouse_id=warehouse_id,
        threshold=threshold,
        skip=skip,
        limit=limit
    )
    
    return [
        {
            "stock_id": s.stock_id,
            "variant_id": s.variant_id,
            "sku": s.variant.sku if s.variant else None,
            "product_name": s.variant.product.product_name if s.variant and s.variant.product else None,
            "quantity": s.quantity,
            "reserved": s.reserved,
            "available": s.available,
            "updated_at": s.updated_at
        }
        for s in stocks
    ]


@router.post("", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("warehouse.manage")),
    warehouse_in: WarehouseCreate,
) -> WarehouseResponse:
    """
    Tạo mới một kho hàng trong hệ thống (Dành cho Admin).
    """
    if warehouse_in.is_default:
        existing_default = await warehouse_crud.get_default(db=db)
        if existing_default:
            existing_default.is_default = False
            db.add(existing_default)
    
    warehouse = await warehouse_crud.create(db=db, obj_in=warehouse_in)
    
    await FastAPICache.clear(namespace="warehouses")
    
    return WarehouseResponse(
        warehouse_id=warehouse.warehouse_id,
        warehouse_name=warehouse.warehouse_name,
        address=warehouse.address,
        city=warehouse.city,
        postal_code=warehouse.postal_code,
        phone=warehouse.phone,
        email=warehouse.email,
        is_active=warehouse.is_active,
        is_default=warehouse.is_default,
        created_at=warehouse.created_at,
        updated_at=warehouse.updated_at
    )


@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("warehouse.manage")),
    warehouse_id: int,
    warehouse_in: WarehouseUpdate,
) -> WarehouseResponse:
    """
    Cập nhật thông tin chi tiết của một kho hàng hiện có.
    """
    warehouse = await warehouse_crud.get(db=db, id=warehouse_id)
    
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    if warehouse_in.is_default and not warehouse.is_default:
        existing_default = await warehouse_crud.get_default(db=db)
        if existing_default and existing_default.warehouse_id != warehouse_id:
            existing_default.is_default = False
            db.add(existing_default)
    
    updated_warehouse = await warehouse_crud.update(
        db=db,
        db_obj=warehouse,
        obj_in=warehouse_in
    )
    
    await FastAPICache.clear(namespace="warehouses")
    
    return WarehouseResponse(
        warehouse_id=updated_warehouse.warehouse_id,
        warehouse_name=updated_warehouse.warehouse_name,
        address=updated_warehouse.address,
        city=updated_warehouse.city,
        postal_code=updated_warehouse.postal_code,
        phone=updated_warehouse.phone,
        email=updated_warehouse.email,
        is_active=updated_warehouse.is_active,
        is_default=updated_warehouse.is_default,
        created_at=updated_warehouse.created_at,
        updated_at=updated_warehouse.updated_at
    )


@router.delete("/{warehouse_id}", response_model=Message)
async def delete_warehouse(
    db: SessionDep,
    warehouse_id: int,
    current_user: User = Depends(require_permission("warehouse.manage")),
) -> Message:
    """
    Xóa vĩnh viễn một kho hàng (Chỉ được xóa khi kho không còn hàng tồn).
    """
    warehouse = await warehouse_crud.get(db=db, id=warehouse_id)
    
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found"
        )
    
    if warehouse.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default warehouse. Set another warehouse as default first."
        )
    
    from app.models.inventory import VariantStock
    from sqlalchemy import select
    
    statement = select(VariantStock).where(VariantStock.warehouse_id == warehouse_id).limit(1)
    result = await db.execute(statement)
    has_stock = result.scalar_one_or_none() is not None
    
    if has_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete warehouse with existing stock. Transfer stock first."
        )
    
    await warehouse_crud.delete(db=db, id=warehouse_id)
    
    await FastAPICache.clear(namespace="warehouses")
    
    return Message(message="Warehouse deleted successfully")


@router.post("/{warehouse_id}/set-default", response_model=WarehouseResponse)
async def set_default_warehouse(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("warehouse.manage")),
    warehouse_id: int,
) -> WarehouseResponse:
    """
    Thiết lập một kho hàng cụ thể làm kho mặc định cho toàn bộ hệ thống.
    """
    try:
        warehouse = await warehouse_crud.set_default(
            db=db,
            warehouse_id=warehouse_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    await FastAPICache.clear(namespace="warehouses")
    
    return WarehouseResponse(
        warehouse_id=warehouse.warehouse_id,
        warehouse_name=warehouse.warehouse_name,
        address=warehouse.address,
        city=warehouse.city,
        postal_code=warehouse.postal_code,
        phone=warehouse.phone,
        email=warehouse.email,
        is_active=warehouse.is_active,
        is_default=warehouse.is_default,
        created_at=warehouse.created_at,
        updated_at=warehouse.updated_at
    )


@router.get("/{warehouse_id}/stock", response_model=List[dict])
@cache(expire=300, namespace="warehouses")
async def get_warehouse_stock(
    db: SessionDep,
    warehouse_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_permission("inventory.view")),
) -> List[dict]:
    """
    Lấy danh sách chi tiết toàn bộ các mặt hàng đang có trong một kho cụ thể.
    """
    from app.crud.inventory import variant_stock as stock_crud
    
    stocks = await stock_crud.get_by_warehouse(
        db=db,
        warehouse_id=warehouse_id,
        skip=skip,
        limit=limit
    )
    
    return [
        {
            "stock_id": s.stock_id,
            "variant_id": s.variant_id,
            "sku": s.variant.sku if s.variant else None,
            "product_name": s.variant.product.product_name if s.variant and s.variant.product else None,
            "quantity": s.quantity,
            "reserved": s.reserved,
            "available": s.available,
            "updated_at": s.updated_at
        }
        for s in stocks
    ]