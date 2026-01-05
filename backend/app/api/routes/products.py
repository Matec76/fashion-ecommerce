from decimal import Decimal

from fastapi import APIRouter, Query, status, HTTPException, Request, Response, Depends, UploadFile, File
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    PaginationDep,
    require_permission,
)
from app.crud.product import product as product_crud
from app.crud.product import product_variant as variant_crud
from app.crud.product import product_image as image_crud
from app.models.product import (
    ProductResponse,
    ProductDetailResponse,
    ProductCreate,
    ProductUpdate,
    ProductVariantResponse,
    ProductVariantCreate,
    ProductVariantUpdate,
    ProductImageResponse,
    ProductImageCreate,
    ProductImageUpdate,
)
from app.models.user import User
from app.models.common import Message
from app.models.enums import ProductGenderEnum
from app.core.config import settings
from app.core.storage import S3Storage
from app.services.mongo_service import mongo_service


router = APIRouter()


def list_products_key_builder(
    func,
    namespace: str = "",
    request: Request = None,
    response: Response = None,
    *args,
    **kwargs,
):
    """
    Tạo key cache cho danh sách sản phẩm dựa trên các tham số truy vấn (query params).
    """
    prefix = f"{FastAPICache.get_prefix()}:{namespace}" if FastAPICache.get_prefix() else namespace
    query_params = sorted(request.query_params.items())
    query_string = "&".join([f"{k}={v}" for k, v in query_params])
    return f"{prefix}:{query_string}" if query_string else f"{prefix}:default"


def product_detail_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho thông tin chi tiết của một sản phẩm theo mã ID.
    """
    prefix = FastAPICache.get_prefix() or ""
    view_kwargs = kwargs.get("kwargs", {})
    product_id = view_kwargs.get("product_id") or kwargs.get("product_id")
    return f"{prefix}:product:detail:{product_id}"


def product_slug_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho thông tin chi tiết của một sản phẩm dựa trên đường dẫn Slug.
    """
    prefix = FastAPICache.get_prefix() or ""
    view_kwargs = kwargs.get("kwargs", {})
    slug = view_kwargs.get("slug") or kwargs.get("slug")
    return f"{prefix}:product:slug:{slug}"


def product_variants_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho danh sách các biến thể (Màu/Size) của một sản phẩm.
    """
    prefix = FastAPICache.get_prefix() or ""
    view_kwargs = kwargs.get("kwargs", {})
    product_id = view_kwargs.get("product_id") or kwargs.get("product_id")
    return f"{prefix}:product:variants:{product_id}"


def product_images_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho thư viện hình ảnh của một sản phẩm cụ thể.
    """
    prefix = FastAPICache.get_prefix() or ""
    view_kwargs = kwargs.get("kwargs", {})
    product_id = view_kwargs.get("product_id") or kwargs.get("product_id")
    return f"{prefix}:product:images:{product_id}"


def product_related_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho danh sách các sản phẩm liên quan.
    """
    prefix = FastAPICache.get_prefix() or ""
    view_kwargs = kwargs.get("kwargs", {})
    product_id = view_kwargs.get("product_id") or kwargs.get("product_id")
    limit = view_kwargs.get("limit", 6)
    return f"{prefix}:product:related:{product_id}:{limit}"



async def invalidate_product_cache(
    product_id: int = None, 
    slug: str = None, 
    clear_lists: bool = True,
    clear_related: bool = False
):
    """
    Xóa bỏ các bản ghi cache liên quan đến sản phẩm khi có sự thay đổi dữ liệu (Thêm/Sửa/Xóa).
    """
    try:
        backend = FastAPICache.get_backend()
        if backend is None:
            return
        
        prefix = FastAPICache.get_prefix() or ""
        
        if product_id:
            keys_to_delete = [
                f"{prefix}:product:detail:{product_id}",
                f"{prefix}:product:variants:{product_id}",
                f"{prefix}:product:images:{product_id}",
            ]
            
            for key in keys_to_delete:
                await backend.delete(key)
            
            if clear_related and hasattr(backend, "redis"):
                pattern = f"{prefix}:product:related:{product_id}*"
                async for match_key in backend.redis.scan_iter(match=pattern):
                    await backend.redis.delete(match_key)
        
        if slug:
            await backend.delete(f"{prefix}:product:slug:{slug}")
        
        if clear_lists and hasattr(backend, "redis"):
            patterns = [
                f"{prefix}:product:list*",
                f"{prefix}:product:list:featured*",
                f"{prefix}:product:list:new*",
                f"{prefix}:product:list:best*",
            ]
            
            for pattern in patterns:
                async for key in backend.redis.scan_iter(match=pattern):
                    await backend.redis.delete(key)
    
    except Exception as e:
        import logging
        logging.warning(f"Lỗi khi xóa cache sản phẩm: {e}")



async def increment_view_count_task(product_id: int):
    """
    Tác vụ chạy ngầm: Tăng số lượt xem (view count) cho sản phẩm để không làm gián đoạn phản hồi API.
    """
    from app.core.db import async_session_maker
    
    async with async_session_maker() as db:
        try:
            await product_crud.increment_view_count(db=db, product_id=product_id)
            await db.commit()
        except Exception as e:
            await db.rollback()
            import logging
            logging.error(f"Lỗi khi tăng view count: {e}")



@router.post("/upload-image", response_model=dict)
async def upload_product_image(
    current_user: User = Depends(require_permission("product.create")),
    file: UploadFile = File(...),
):
    """
    Tải lên hình ảnh sản phẩm lên kho lưu trữ S3 trước khi gán vào sản phẩm.
    """
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File không hợp lệ. Chỉ chấp nhận: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        limit_mb = settings.MAX_UPLOAD_SIZE / 1024 / 1024
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File quá lớn (Max {int(limit_mb)}MB)"
        )

    try:
        result = await S3Storage.upload_file(
            file=file.file,
            filename=file.filename,
            folder=settings.S3_PRODUCT_IMAGES_FOLDER,
            content_type=file.content_type,
        )

        final_url = result.get("cdn_url") or result["file_url"]

        return {"url": final_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload: {str(e)}")
    

@router.get("", response_model=list[ProductResponse])
@cache(expire=300, namespace="product:list", key_builder=list_products_key_builder)
async def list_products(
    db: SessionDep,
    pagination: PaginationDep,
    search: str | None = Query(None, description="Từ khóa tìm kiếm"),
    category_id: int | None = Query(None, description="Lọc theo ID danh mục"),
    brand: str | None = Query(None, description="Lọc theo thương hiệu"),
    gender: ProductGenderEnum | None = Query(None, description="Lọc theo giới tính"),
    min_price: float | None = Query(None, ge=0, description="Giá tối thiểu"),
    max_price: float | None = Query(None, ge=0, description="Giá tối đa"),
    is_featured: bool | None = Query(None, description="Lọc sản phẩm nổi bật"),
    sort_by: str | None = Query(
        None,
        description="Sắp xếp theo: created_at, price_asc, price_desc, name, rating, popularity, best_selling"
    ),
) -> list[ProductResponse]:
    """
    Lấy danh sách các sản phẩm đang hoạt động với đầy đủ các bộ lọc và tùy chọn sắp xếp.
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Giá tối thiểu phải nhỏ hơn hoặc bằng giá tối đa"
        )
    
    min_price_decimal = Decimal(str(min_price)) if min_price is not None else None
    max_price_decimal = Decimal(str(max_price)) if max_price is not None else None
    
    if search:
        products = await product_crud.search(
            db=db,
            query=search,
            skip=pagination.get_offset(),
            limit=pagination.get_limit(),
            category_id=category_id,
            brand=brand,
            gender=gender,
            min_price=min_price_decimal,
            max_price=max_price_decimal,
            is_featured=is_featured,
            sort_by=sort_by,
        )
    else:
        products = await product_crud.get_active(
            db=db,
            skip=pagination.get_offset(),
            limit=pagination.get_limit(),
            category_id=category_id,
            brand=brand,
            gender=gender,
            min_price=min_price_decimal,
            max_price=max_price_decimal,
            is_featured=is_featured,
            sort_by=sort_by,
        )
    
    return products


@router.get("/featured", response_model=list[ProductResponse])
@cache(expire=600, namespace="product:list:featured", key_builder=list_products_key_builder)
async def get_featured_products(
    db: SessionDep,
    category_id: int | None = Query(None, description="Lọc sản phẩm nổi bật theo ID danh mục"),
    limit: int = Query(10, ge=1, le=50),
) -> list[ProductResponse]:
    """
    Lấy danh sách các sản phẩm nổi bật thường được trưng bày trên trang chủ.
    """
    products = await product_crud.get_featured(db=db, limit=limit, category_id=category_id)
    return products


@router.get("/new-arrivals", response_model=list[ProductResponse])
@cache(expire=300, namespace="product:list:new", key_builder=list_products_key_builder)
async def get_new_arrivals(
    db: SessionDep,
    category_id: int | None = Query(None, description="Lọc sản phẩm mới theo ID danh mục"),
    limit: int = Query(10, ge=1, le=50),
) -> list[ProductResponse]:
    """
    Lấy danh sách các sản phẩm mới nhất vừa được thêm vào hệ thống.
    """
    products = await product_crud.get_new_arrivals(db=db, limit=limit, category_id=category_id)
    return products


@router.get("/best-sellers", response_model=list[ProductResponse])
@cache(expire=600, namespace="product:list:best", key_builder=list_products_key_builder)
async def get_best_sellers(
    db: SessionDep,
    category_id: int | None = Query(None, description="Lọc sản phẩm bán chạy theo ID danh mục"),
    limit: int = Query(10, ge=1, le=50),
) -> list[ProductResponse]:
    """
    Lấy danh sách các sản phẩm có doanh số bán ra cao nhất.
    """
    products = await product_crud.get_best_sellers(db=db, limit=limit, category_id=category_id)
    return products



@router.get("/{product_id}", response_model=ProductDetailResponse)
@cache(expire=300, key_builder=product_detail_key_builder)
async def get_product(
    db: SessionDep,
    product_id: int,
) -> ProductDetailResponse:
    """
    Xem thông tin chi tiết một sản phẩm theo ID (Bao gồm các biến thể và hình ảnh).
    """
    product = await product_crud.get_with_details(db=db, id=product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    return product


@router.get("/slug/{slug}", response_model=ProductDetailResponse)
@cache(expire=300, key_builder=product_slug_key_builder)
async def get_product_by_slug(
    db: SessionDep,
    slug: str,
) -> ProductDetailResponse:
    """
    Truy vấn thông tin chi tiết sản phẩm dựa trên đường dẫn Slug thân thiện với SEO.
    """
    product = await product_crud.get_by_slug(db=db, slug=slug)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    product_detail = await product_crud.get_with_details(
        db=db, 
        id=product.product_id
    )
    
    return product_detail


@router.get("/{product_id}/related", response_model=list[ProductResponse])
@cache(expire=600, key_builder=product_related_key_builder)
async def get_related_products(
    db: SessionDep,
    product_id: int,
    limit: int = Query(6, ge=1, le=20),
) -> list[ProductResponse]:
    """
    Lấy danh sách các sản phẩm liên quan hoặc cùng loại với sản phẩm đang xem.
    """
    product = await product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    related = await product_crud.get_related_products(
        db=db,
        product_id=product_id,
        limit=limit
    )
    return related



@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("product.create")),
    product_in: ProductCreate,
) -> ProductResponse:
    """
    Tạo một hồ sơ sản phẩm mới trên hệ thống (Dành cho Admin).
    """
    if product_in.slug:
        existing = await product_crud.get_by_slug(db=db, slug=product_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug sản phẩm đã tồn tại"
            )
    
    product = await product_crud.create(db=db, obj_in=product_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "CREATE_PRODUCT",
        "details": f"Admin {current_user.email} tạo sản phẩm: {product.product_name} (ID: {product.product_id})"
    })

    await invalidate_product_cache(clear_lists=True)
    
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("product.update")),
    product_id: int,
    product_in: ProductUpdate,
) -> ProductResponse:
    """
    Cập nhật các thông tin cơ bản của một sản phẩm (Dành cho Admin).
    """
    product = await product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    if product_in.slug and product_in.slug != product.slug:
        existing = await product_crud.get_by_slug(db=db, slug=product_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug sản phẩm đã tồn tại"
            )
    
    updated_product = await product_crud.update(db=db, db_obj=product, obj_in=product_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "UPDATE_PRODUCT",
        "target_id": product_id,
        "details": f"Admin {current_user.email} cập nhật thông tin sản phẩm ID {product_id}"
    })
    
    old_slug = product.slug if product_in.slug and product_in.slug != product.slug else None
    await invalidate_product_cache(
        product_id=product_id,
        slug=old_slug,
        clear_lists=True,
        clear_related=True
    )
    
    return updated_product


@router.delete("/{product_id}", response_model=Message)
async def delete_product(
    db: SessionDep,
    product_id: int,
    current_user: User = Depends(require_permission("product.delete")),
    permanent: bool = Query(False, description="Xóa vĩnh viễn (True) hoặc Xóa mềm (False)"),
) -> Message:
    """
    Xóa sản phẩm khỏi hệ thống (Hỗ trợ Xóa mềm bằng cách vô hiệu hóa).
    """
    product = await product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    product_slug = product.slug
    
    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_PRODUCT",
        "is_permanent": permanent,
        "details": f"Admin {current_user.email} đã {'xóa vĩnh viễn' if permanent else 'vô hiệu hóa'} sản phẩm ID {product_id}"
    })
    
    if permanent:
        await product_crud.delete(db=db, id=product_id, soft_delete=False)
        msg = "Đã xóa vĩnh viễn sản phẩm"
    else:
        await product_crud.update(db=db, db_obj=product, obj_in={"is_active": False})
        msg = "Đã vô hiệu hóa sản phẩm (Soft Delete)"
    
    await invalidate_product_cache(
        product_id=product_id,
        slug=product_slug,
        clear_lists=True,
        clear_related=True
    )
    
    return Message(message=msg)



@router.get("/{product_id}/variants", response_model=list[ProductVariantResponse])
@cache(expire=300, key_builder=product_variants_key_builder)
async def get_product_variants(
    db: SessionDep,
    product_id: int,
) -> list[ProductVariantResponse]:
    """
    Lấy danh sách chi tiết tất cả các biến thể có sẵn của một sản phẩm.
    """
    product = await product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    variants = await variant_crud.get_by_product(db=db, product_id=product_id)
    return variants


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_product_variant(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("product.update")),
    product_id: int,
    variant_in: ProductVariantCreate,
) -> ProductVariantResponse:
    """
    Thêm mới một biến thể sản phẩm (như Kích thước hoặc Màu sắc mới) (Dành cho Admin).
    """
    product = await product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    existing = await variant_crud.get_by_sku(db=db, sku=variant_in.sku)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mã SKU này đã tồn tại"
        )
    
    variant_data = variant_in.model_dump()
    variant_data["product_id"] = product_id
    variant = await variant_crud.create(db=db, obj_in=variant_data)
    
    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "CREATE_VARIANT",
        "target_id": variant.variant_id,
        "details": f"Admin {current_user.email} đã tạo biến thể mới cho sản phẩm ID {product_id}. SKU: {variant.sku}"
    })

    await invalidate_product_cache(product_id=product_id, clear_lists=False)
    
    return variant


@router.patch("/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_product_variant(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("product.update")),
    variant_id: int,
    variant_in: ProductVariantUpdate,
) -> ProductVariantResponse:
    """
    Chỉnh sửa thông tin của một biến thể sản phẩm hiện có (Dành cho Admin).
    """
    variant = await variant_crud.get(db=db, id=variant_id)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy biến thể"
        )
    
    if variant_in.sku and variant_in.sku != variant.sku:
        existing = await variant_crud.get_by_sku(db=db, sku=variant_in.sku)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã SKU này đã tồn tại"
            )
    
    updated_variant = await variant_crud.update(db=db, db_obj=variant, obj_in=variant_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "UPDATE_VARIANT",
        "target_id": variant_id,
        "details": f"Admin {current_user.email} đã cập nhật biến thể ID {variant_id}"
    })
    
    await invalidate_product_cache(product_id=variant.product_id, clear_lists=False)
    
    return updated_variant


@router.delete("/variants/{variant_id}", response_model=Message)
async def delete_product_variant(
    db: SessionDep,
    variant_id: int,
    current_user: User = Depends(require_permission("product.update")),
) -> Message:
    """
    Xóa bỏ một biến thể sản phẩm khỏi hệ thống (Dành cho Admin).
    """
    variant = await variant_crud.get(db=db, id=variant_id)
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy biến thể"
        )
    
    product_id = variant.product_id
    await variant_crud.delete(db=db, id=variant_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_VARIANT",
        "target_id": variant_id,
        "details": f"Admin {current_user.email} đã xóa biến thể ID {variant_id} của sản phẩm ID {product_id}"
    })
    
    await invalidate_product_cache(product_id=product_id, clear_lists=False)
    
    return Message(message="Xóa biến thể thành công")



@router.get("/{product_id}/images", response_model=list[ProductImageResponse])
@cache(expire=600, key_builder=product_images_key_builder)
async def get_product_images(
    db: SessionDep,
    product_id: int,
) -> list[ProductImageResponse]:
    """
    Lấy toàn bộ danh sách hình ảnh đi kèm của một sản phẩm.
    """
    product = await product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    images = await image_crud.get_by_product(db=db, product_id=product_id)
    return images


@router.post("/{product_id}/images", response_model=ProductImageResponse, status_code=status.HTTP_201_CREATED)
async def create_product_image(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("product.update")),
    product_id: int,
    image_in: ProductImageCreate,
) -> ProductImageResponse:
    """
    Gán thêm hình ảnh mới cho một sản phẩm (Dành cho Admin).
    """
    product = await product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy sản phẩm"
        )
    
    image_data = image_in.model_dump()
    image_data["product_id"] = product_id
    image = await image_crud.create(db=db, obj_in=image_data)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "CREATE_PRODUCT_IMAGE",
        "target_id": image.image_id,
        "details": f"Admin {current_user.email} đã thêm hình ảnh cho sản phẩm ID {product_id}"
    })
    
    await invalidate_product_cache(product_id=product_id, clear_lists=False)
    
    return image


@router.patch("/images/{image_id}", response_model=ProductImageResponse)
async def update_product_image(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("product.update")),
    image_id: int,
    image_in: ProductImageUpdate,
) -> ProductImageResponse:
    """
    Cập nhật các thông tin mô tả của hình ảnh (như thứ tự hiển thị hoặc văn bản thay thế) (Dành cho Admin).
    """
    image = await image_crud.get(db=db, id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hình ảnh"
        )
    
    updated_image = await image_crud.update(db=db, db_obj=image, obj_in=image_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "UPDATE_PRODUCT_IMAGE",
        "target_id": image_id,
        "details": f"Admin {current_user.email} đã cập nhật hình ảnh ID {image_id} của sản phẩm ID {image.product_id}"
    })
    
    await invalidate_product_cache(product_id=image.product_id, clear_lists=False)
    
    return updated_image


@router.delete("/images/{image_id}", response_model=Message)
async def delete_product_image(
    db: SessionDep,
    image_id: int,
    current_user: User = Depends(require_permission("product.update")),
) -> Message:
    """
    Xóa vĩnh viễn một hình ảnh khỏi sản phẩm (Dành cho Admin).
    """
    image = await image_crud.get(db=db, id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hình ảnh"
        )
    
    product_id = image.product_id
    await image_crud.delete(db=db, id=image_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_PRODUCT_IMAGE",
        "target_id": image_id,
        "details": f"Admin {current_user.email} đã xóa hình ảnh ID {image_id} khỏi sản phẩm ID {product_id}"
    })
    
    await invalidate_product_cache(product_id=product_id, clear_lists=False)
    
    return Message(message="Xóa hình ảnh thành công")


@router.post("/images/{image_id}/set-primary", response_model=ProductImageResponse)
async def set_primary_image(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("product.update")),
    image_id: int,
) -> ProductImageResponse:
    """
    Thiết lập một hình ảnh cụ thể làm ảnh đại diện chính cho sản phẩm (Dành cho Admin).
    """
    image = await image_crud.get(db=db, id=image_id)
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy hình ảnh"
        )
    
    updated_image = await image_crud.set_primary(
        db=db,
        image_id=image_id,
        product_id=image.product_id
    )
    
    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "SET_PRIMARY_IMAGE",
        "target_id": image_id,
        "details": f"Admin {current_user.email} đã đặt ảnh ID {image_id} làm ảnh đại diện cho sản phẩm ID {image.product_id}"
    })

    await invalidate_product_cache(product_id=image.product_id, clear_lists=True)
    
    return updated_image