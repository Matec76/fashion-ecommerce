import logging
from typing import List

from fastapi import APIRouter, Query, status, HTTPException, Request, Depends
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from app.api.deps import (
    SessionDep,
    CurrentUser,
    PaginationDep,
    require_permission,
)
from app.crud.coupon import coupon as coupon_crud
from app.crud.coupon import flash_sale as flash_sale_crud
from app.crud.coupon import flash_sale_product as flash_sale_product_crud
from app.crud.loyalty import loyalty_point_crud
from app.models.coupon import (
    CouponResponse,
    CouponCreate,
    CouponUpdate,
    CouponValidation,
    CouponValidationResponse,
    FlashSaleResponse,
    FlashSaleDetailResponse,
    FlashSaleCreate,
    FlashSaleUpdate,
    FlashSaleProductAdd,
)
from app.models.common import Message
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


async def invalidate_coupon_cache():
    """
    Xóa toàn bộ bộ nhớ đệm (cache) liên quan đến mã giảm giá và chương trình khuyến mãi.
    """
    try:
        namespaces = [
            "coupons:public", 
            "coupons:admin", 
            "coupons:detail",
            "flash_sales:active",
            "flash_sales:upcoming",
            "flash_sales:admin",
            "flash_sales:detail",
            "flash_sales:check"
        ]
        
        for ns in namespaces:
            await FastAPICache.clear(namespace=ns)
            
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")


@router.get("/public", response_model=List[CouponResponse])
@cache(expire=600, namespace="coupons:public")
async def get_public_coupons(
    db: SessionDep,
    limit: int = Query(10, ge=1, le=50, description="Number of coupons"),
) -> List[CouponResponse]:
    """
    Lấy danh sách các mã giảm giá đang ở trạng thái công khai cho khách hàng.
    """
    coupons = await coupon_crud.get_public_coupons(db=db, limit=limit)
    return coupons


@router.get("/available", response_model=List[CouponResponse])
async def get_available_coupons(
    db: SessionDep,
    current_user: CurrentUser, 
):
    """
    Lấy danh sách mã giảm giá khả dụng cho user (Bao gồm: Public + Tier + Private).
    """
    user_loyalty = await loyalty_point_crud.get_by_user(db=db, user_id=current_user.user_id)
    
    if user_loyalty and user_loyalty.tier:
        user_tier = user_loyalty.tier.tier_name.upper()
    else:
        user_tier = "BRONZE"
    
    coupons = await coupon_crud.get_coupons_for_user(
        db=db, 
        user_id=current_user.user_id, 
        user_tier=user_tier
    )
    
    return coupons


@router.post("/validate", response_model=CouponValidationResponse)
async def validate_coupon(
    db: SessionDep,
    current_user: CurrentUser,
    validation_in: CouponValidation,
) -> CouponValidationResponse:
    """
    Kiểm tra tính hợp lệ của mã giảm giá và tính toán số tiền được giảm dựa trên giá trị đơn hàng.
    """
    result = await coupon_crud.validate_coupon(
        db=db,
        code=validation_in.coupon_code,
        user_id=current_user.user_id,
        order_amount=validation_in.order_total
    )
    
    return CouponValidationResponse(
        is_valid=result.valid,
        discount_amount=result.discount_amount,
        message=result.error,
        coupon=result.coupon
    )


@router.get("", response_model=List[CouponResponse])
@cache(expire=300, namespace="coupons:admin")
async def list_coupons(
    request: Request,
    db: SessionDep,
    pagination: PaginationDep,
    current_user: User = Depends(require_permission("marketing.view")),
    is_active: bool | None = Query(None, description="Filter by active status"),
) -> List[CouponResponse]:
    """
    Liệt kê danh sách tất cả các mã giảm giá (Dành cho Admin - Hỗ trợ phân trang và lọc).
    """
    if is_active is not None:
        coupons = await coupon_crud.get_multi(
            db=db,
            skip=pagination.get_offset(),
            limit=pagination.get_limit(),
            filters={"is_active": is_active}
        )
    else:
        coupons = await coupon_crud.get_multi(
            db=db,
            skip=pagination.get_offset(),
            limit=pagination.get_limit()
        )
    
    return coupons


@router.get("/{coupon_id}", response_model=CouponResponse)
@cache(expire=300, namespace="coupons:detail")
async def get_coupon(
    db: SessionDep,
    coupon_id: int,
    current_user: User = Depends(require_permission("marketing.view")),
) -> CouponResponse:
    """
    Xem thông tin chi tiết của một mã giảm giá dựa trên ID (Dành cho Admin quản lý).
    """
    coupon = await coupon_crud.get(db=db, id=coupon_id)
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    return coupon


@router.get("/code/{coupon_code}", response_model=CouponResponse)
@cache(expire=300, namespace="coupons:detail")
async def get_coupon_by_code(
    db: SessionDep,
    coupon_code: str,
    current_user: User = Depends(require_permission("marketing.view")),
) -> CouponResponse:
    """
    Tìm kiếm và lấy thông tin mã giảm giá dựa trên mã code văn bản (Dành cho Admin quản lý).
    """
    coupon = await coupon_crud.get_by_code(db=db, code=coupon_code)
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    return coupon


@router.post("", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("marketing.manage")),
    coupon_in: CouponCreate,
) -> CouponResponse:
    """
    Tạo mới một mã giảm giá vào hệ thống (Dành cho Admin quản lý).
    """
    existing = await coupon_crud.get_by_code(db=db, code=coupon_in.coupon_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon code already exists"
        )
    
    coupon = await coupon_crud.create(db=db, obj_in=coupon_in)
    await invalidate_coupon_cache()
    
    return coupon


@router.patch("/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("marketing.manage")),
    coupon_id: int,
    coupon_in: CouponUpdate,
) -> CouponResponse:
    """
    Cập nhật thông tin cấu hình của một mã giảm giá hiện có (Dành cho Admin quản lý).
    """
    coupon = await coupon_crud.get(db=db, id=coupon_id)
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    updated_coupon = await coupon_crud.update(
        db=db,
        db_obj=coupon,
        obj_in=coupon_in
    )
    
    await invalidate_coupon_cache()
    return updated_coupon


@router.delete("/{coupon_id}", response_model=Message)
async def delete_coupon(
    db: SessionDep,
    coupon_id: int,
    current_user: User = Depends(require_permission("marketing.manage")),
) -> Message:
    """
    Xóa vĩnh viễn một mã giảm giá khỏi hệ thống (Dành cho Admin quản lý).
    """
    coupon = await coupon_crud.get(db=db, id=coupon_id)
    
    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coupon not found"
        )
    
    await coupon_crud.delete(db=db, id=coupon_id)
    await invalidate_coupon_cache()
    
    return Message(message="Coupon deleted successfully")


@router.get("/flash-sales/active", response_model=List[FlashSaleResponse])
@cache(expire=300, namespace="flash_sales:active")
async def get_active_flash_sales(
    db: SessionDep,
) -> List[FlashSaleResponse]:
    """
    Lấy danh sách các chương trình Flash Sale đang diễn ra trong thời điểm hiện tại.
    """
    flash_sales = await flash_sale_crud.get_active(db=db, limit=10)
    
    return flash_sales


@router.get("/flash-sales/upcoming", response_model=List[FlashSaleResponse])
@cache(expire=600, namespace="flash_sales:upcoming")
async def get_upcoming_flash_sales(
    db: SessionDep,
    limit: int = Query(5, ge=1, le=20),
) -> List[FlashSaleResponse]:
    """
    Lấy danh sách các chương trình Flash Sale sắp diễn ra trong tương lai.
    """
    flash_sales = await flash_sale_crud.get_upcoming(db=db, limit=limit)
    
    for sale in flash_sales:
        sale.product_count = len(sale.flash_sale_products)
    
    return flash_sales


@router.get("/flash-sales/all", response_model=List[FlashSaleResponse])
@cache(expire=300, namespace="flash_sales:admin")
async def list_flash_sales(
    request: Request,
    db: SessionDep,
    pagination: PaginationDep,
    current_user: User = Depends(require_permission("marketing.view")),
) -> List[FlashSaleResponse]:
    """
    Liệt kê tất cả các sự kiện Flash Sale (Dành cho Admin quản lý).
    """
    flash_sales = await flash_sale_crud.get_multi(
        db=db,
        skip=pagination.get_offset(),
        limit=pagination.get_limit(),
        order_by="start_time",
        order_desc=True
    )
    
    return flash_sales


@router.get("/flash-sales/{flash_sale_id}", response_model=FlashSaleDetailResponse)
@cache(expire=300, namespace="flash_sales:detail")
async def get_flash_sale(
    db: SessionDep,
    flash_sale_id: int,
) -> FlashSaleDetailResponse:
    """
    Xem thông tin chi tiết của một sự kiện Flash Sale bao gồm cả danh sách sản phẩm tham gia.
    """
    flash_sale = await flash_sale_crud.get_with_products(
        db=db,
        flash_sale_id=flash_sale_id
    )
    
    if not flash_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flash sale not found"
        )
    
    return flash_sale


@router.post("/flash-sales", response_model=FlashSaleResponse, status_code=status.HTTP_201_CREATED)
async def create_flash_sale(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("marketing.manage")),
    flash_sale_in: FlashSaleCreate,
) -> FlashSaleResponse:
    """
    Tạo một chương trình Flash Sale mới và thêm sản phẩm nếu có yêu cầu (Dành cho Admin quản lý).
    """
    flash_sale = await flash_sale_crud.create(db=db, obj_in=flash_sale_in)
    
    product_count = 0
    if hasattr(flash_sale_in, 'product_ids') and flash_sale_in.product_ids:
        try:
            for product_id in flash_sale_in.product_ids:
                await flash_sale_product_crud.add_product(
                    db=db,
                    flash_sale_id=flash_sale.flash_sale_id,
                    product_id=product_id
                )
                product_count += 1
        except Exception as e:
            logger.error(f"Error adding products to flash sale: {e}")
    
    flash_sale.product_count = product_count
    
    await invalidate_coupon_cache()
    return flash_sale


@router.patch("/flash-sales/{flash_sale_id}", response_model=FlashSaleResponse)
async def update_flash_sale(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("marketing.manage")),
    flash_sale_id: int,
    flash_sale_in: FlashSaleUpdate,
) -> FlashSaleResponse:
    """
    Cập nhật thời gian hoặc cấu hình của một chương trình Flash Sale (Dành cho Admin quản lý).
    """
    flash_sale = await flash_sale_crud.get(db=db, id=flash_sale_id)
    
    if not flash_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flash sale not found"
        )
    
    updated_flash_sale = await flash_sale_crud.update(
        db=db,
        db_obj=flash_sale,
        obj_in=flash_sale_in
    )
    
    await invalidate_coupon_cache()
    return updated_flash_sale


@router.delete("/flash-sales/{flash_sale_id}", response_model=Message)
async def delete_flash_sale(
    db: SessionDep,
    flash_sale_id: int,
    current_user: User = Depends(require_permission("marketing.manage")),
) -> Message:
    """
    Xóa bỏ một sự kiện Flash Sale khỏi hệ thống (Dành cho Admin quản lý).
    """
    flash_sale = await flash_sale_crud.get(db=db, id=flash_sale_id)
    
    if not flash_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flash sale not found"
        )
    
    await flash_sale_crud.delete(db=db, id=flash_sale_id)
    await invalidate_coupon_cache()
    
    return Message(message="Flash sale deleted successfully")


@router.post("/flash-sales/{flash_sale_id}/products", response_model=Message)
async def add_product_to_flash_sale(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("marketing.manage")),
    flash_sale_id: int,
    product_data: FlashSaleProductAdd,
) -> Message:
    """
    Thêm một sản phẩm cụ thể và giới hạn số lượng tham gia vào chương trình Flash Sale (Dành cho Admin quản lý).
    """
    flash_sale = await flash_sale_crud.get(db=db, id=flash_sale_id)
    if not flash_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flash sale not found"
        )
    
    await flash_sale_product_crud.add_product(
        db=db,
        flash_sale_id=flash_sale_id,
        product_id=product_data.product_id,
        quantity_limit=product_data.quantity_limit
    )
    
    await invalidate_coupon_cache()
    return Message(message="Product added to flash sale successfully")


@router.delete("/flash-sales/{flash_sale_id}/products/{product_id}", response_model=Message)
async def remove_product_from_flash_sale(
    db: SessionDep,
    flash_sale_id: int,
    product_id: int,
    current_user: User = Depends(require_permission("marketing.manage")),
) -> Message:
    """
    Xóa bỏ một sản phẩm ra khỏi chương trình Flash Sale hiện có (Dành cho Admin quản lý).
    """
    success = await flash_sale_product_crud.remove_product(
        db=db,
        flash_sale_id=flash_sale_id,
        product_id=product_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in flash sale"
        )
    
    await invalidate_coupon_cache()
    return Message(message="Product removed from flash sale successfully")


@router.get("/flash-sales/product/{product_id}/check", response_model=dict)
@cache(expire=300, namespace="flash_sales:check")
async def check_product_in_flash_sale(
    db: SessionDep,
    product_id: int,
) -> dict:
    """
    Kiểm tra xem một sản phẩm cụ thể có đang nằm trong chương trình Flash Sale nào không.
    """
    flash_sale = await flash_sale_crud.check_active_for_product(
        db=db,
        product_id=product_id
    )
    
    if flash_sale:
        return {
            "in_flash_sale": True,
            "flash_sale": {
                "flash_sale_id": flash_sale.flash_sale_id,
                "sale_name": flash_sale.sale_name,
                "discount_type": flash_sale.discount_type,
                "discount_value": flash_sale.discount_value,
                "end_time": flash_sale.end_time,
            }
        }
    
    return {"in_flash_sale": False}