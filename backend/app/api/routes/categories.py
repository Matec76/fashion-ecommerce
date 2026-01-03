from typing import Any
from fastapi import APIRouter, Query, status, HTTPException, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    require_permission,
)
from app.crud.category import category as category_crud
from app.crud.category import product_collection as collection_crud
from app.models.category import (
    CategoryResponse,
    CategoryWithChildrenResponse,
    CategoryTreeResponse,
    CategoryCreate,
    CategoryUpdate,
    CollectionResponse,
    CollectionWithProductsResponse,
    CollectionCreate,
    CollectionUpdate,
    CollectionProductAdd,
)
from app.models.common import Message
from app.models.user import User
from sqlalchemy import select
from fastapi import UploadFile, File
from app.core.config import settings
from app.core.storage import S3Storage

router = APIRouter()


@router.post("/upload-image", response_model=dict)
async def upload_category_image(
    current_user: User = Depends(require_permission("category.manage")),
    file: UploadFile = File(...),
):
    """
    Tải lên hình ảnh minh họa cho danh mục (Banner/Icon).
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
            folder=settings.S3_CATEGORIES_IMAGES_FOLDER,
            content_type=file.content_type,
        )

        final_url = result.get("cdn_url") or result["file_url"]

        return {"url": final_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload: {str(e)}")


@router.get("", response_model=list[CategoryResponse])
@cache(expire=3600, namespace="categories")
async def list_categories(
    db: SessionDep,
    parent_id: int | None = Query(None, description="Filter by parent category"),
    is_active: bool = Query(True, description="Filter by active status"),
) -> list[CategoryResponse]:
    """
    Lấy danh sách các danh mục (Có lọc theo danh mục cha và trạng thái hoạt động).
    """
    if parent_id is not None:
        categories = await category_crud.get_children(
            db=db,
            parent_id=parent_id,
            is_active=is_active
        )
    else:
        categories = await category_crud.get_root_categories(
            db=db,
            is_active=is_active
        )
    
    return categories


@router.get("/tree", response_model=list[CategoryTreeResponse])
@cache(expire=7200, namespace="categories")
async def get_category_tree(
    db: SessionDep,
    is_active: bool = Query(True, description="Filter by active status"),
) -> list[dict]:
    """
    Lấy toàn bộ cấu trúc cây danh mục sản phẩm.
    """
    tree = await category_crud.get_tree(db=db, is_active=is_active)
    return tree


@router.get("/{category_id}", response_model=CategoryWithChildrenResponse)
@cache(expire=3600, namespace="categories")
async def get_category(
    db: SessionDep,
    category_id: int,
) -> CategoryWithChildrenResponse:
    """
    Xem thông tin chi tiết của một danh mục và các danh mục con trực thuộc.
    """
    category = await category_crud.get_with_children(db=db, id=category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.get("/slug/{slug}", response_model=CategoryWithChildrenResponse)
@cache(expire=3600, namespace="categories")
async def get_category_by_slug(
    db: SessionDep,
    slug: str,
) -> CategoryWithChildrenResponse:
    """
    Tìm kiếm thông tin danh mục dựa trên đường dẫn slug.
    """
    category = await category_crud.get_by_slug(db=db, slug=slug)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category_with_children = await category_crud.get_with_children(
        db=db,
        id=category.category_id
    )
    
    return category_with_children


@router.get("/{category_id}/breadcrumb", response_model=list[CategoryResponse])
@cache(expire=3600, namespace="categories")
async def get_category_breadcrumb(
    db: SessionDep,
    category_id: int,
) -> list[CategoryResponse]:
    """
    Lấy danh sách các danh mục cha (đường dẫn breadcrumb) cho một danh mục cụ thể.
    """
    breadcrumb = await category_crud.get_breadcrumbs(db=db, category_id=category_id)
    
    if not breadcrumb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return breadcrumb


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("category.manage")),
    category_in: CategoryCreate,
) -> CategoryResponse:
    """
    Tạo một danh mục mới (Dành cho Admin).
    """
    if category_in.slug:
        existing = await category_crud.get_by_slug(db=db, slug=category_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this slug already exists"
            )
    
    if category_in.parent_category_id:
        parent = await category_crud.get(db=db, id=category_in.parent_category_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )
    
    category = await category_crud.create(db=db, obj_in=category_in)
    
    await FastAPICache.clear(namespace="categories")
    
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("category.manage")),
    category_id: int,
    category_in: CategoryUpdate,
) -> CategoryResponse:
    """
    Cập nhật thông tin danh mục hiện có (Dành cho Admin).
    """
    category = await category_crud.get(db=db, id=category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if category_in.parent_category_id:
        if category_in.parent_category_id == category_id:
            raise HTTPException(
                status_code=400, 
                detail="Danh mục không thể là cha của chính nó"
            )
        
        is_invalid = await category_crud.is_descendant(
            db=db, 
            parent_id=category_id, 
            child_id=category_in.parent_category_id
        )
        if is_invalid:
            raise HTTPException(
                status_code=400, 
                detail="Không thể chọn danh mục con làm danh mục cha"
            )
    
    if category_in.slug and category_in.slug != category.slug:
        existing = await category_crud.get_by_slug(db=db, slug=category_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category with this slug already exists"
            )
    
    if category_in.parent_category_id is not None:
        if category_in.parent_category_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )
        
        if category_in.parent_category_id:
            parent = await category_crud.get(db=db, id=category_in.parent_category_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found"
                )
    
    updated_category = await category_crud.update(
        db=db,
        db_obj=category,
        obj_in=category_in
    )
    
    await FastAPICache.clear(namespace="categories")
    
    return updated_category


@router.delete("/{category_id}", response_model=Message)
async def delete_category(
    db: SessionDep,
    category_id: int,
    current_user: User = Depends(require_permission("category.manage")),
) -> Message:
    """
    Xóa danh mục (Chỉ được xóa nếu không có danh mục con trực thuộc).
    """
    category = await category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    children = await category_crud.get_children(db=db, parent_id=category_id)
    if children:
        raise HTTPException(status_code=400, detail="Phải xóa các danh mục con trước")


    from sqlalchemy import func
    from app.models.product import Product

    stmt = select(func.count(Product.product_id)).where(Product.category_id == category_id)
    count_res = await db.execute(stmt)
    if count_res.scalar() > 0:
        raise HTTPException(status_code=400, detail="Danh mục còn sản phẩm, không thể xóa")

    await category_crud.delete(db=db, id=category_id)
    await FastAPICache.clear(namespace="categories")
    return Message(message="Category deleted successfully")


@router.post("/{category_id}/move", response_model=CategoryResponse)
async def move_category(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("category.manage")),
    category_id: int,
    new_parent_id: int | None = Query(None, description="New parent ID (null = root)"),
) -> CategoryResponse:
    """
    Di chuyển danh mục sang một danh mục cha khác.
    """

    if new_parent_id:
        if new_parent_id == category_id:
            raise HTTPException(status_code=400, detail="Danh mục không thể làm cha chính nó")
            
        is_invalid = await category_crud.is_descendant(
            db=db, parent_id=category_id, child_id=new_parent_id
        )
        if is_invalid:
            raise HTTPException(status_code=400, detail="Không thể di chuyển danh mục cha vào làm con của danh mục con")

    category = await category_crud.move_category(
        db=db,
        category_id=category_id,
        new_parent_id=new_parent_id
    )
    
    await FastAPICache.clear(namespace="categories")
    
    return category


@router.post("/collections/upload-image", response_model=dict)
async def upload_collection_image(
    current_user: User = Depends(require_permission("collection.manage")),
    file: UploadFile = File(...),
):
    """
    Tải lên hình ảnh banner/thumbnail cho bộ sưu tập (Collection).
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
            folder=settings.S3_COLLECTIONS_IMAGES_FOLDER, 
            content_type=file.content_type,
        )

        final_url = result.get("cdn_url") or result["file_url"]

        return {"url": final_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload: {str(e)}")


@router.get("/collections/all", response_model=list[CollectionResponse])
@cache(expire=1800, namespace="collections")
async def list_collections(
    db: SessionDep,
    is_active: bool = Query(True, description="Filter by active status"),
) -> list[CollectionResponse]:
    """
    Lấy danh sách tất cả các bộ sưu tập sản phẩm.
    """
    collections = await collection_crud.get_active(db=db) if is_active else await collection_crud.get_multi(db=db, limit=100)
    return collections


@router.get("/collections/{collection_id}", response_model=CollectionWithProductsResponse)
@cache(expire=1800, namespace="collections")
async def get_collection(
    db: SessionDep,
    collection_id: int,
) -> CollectionWithProductsResponse:
    """
    Xem thông tin chi tiết của một bộ sưu tập và danh sách sản phẩm đi kèm.
    """
    collection = await collection_crud.get_with_products(db=db, collection_id=collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    return collection


@router.get("/collections/slug/{slug}", response_model=CollectionWithProductsResponse)
@cache(expire=1800, namespace="collections")
async def get_collection_by_slug(
    db: SessionDep,
    slug: str,
) -> Any:
    """
    Lấy thông tin bộ sưu tập và danh sách sản phẩm dựa trên slug.
    """
    collection_obj = await collection_crud.get_by_slug(db=db, slug=slug)
    
    if not collection_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    collection_data = await collection_crud.get_with_products(
        db=db, 
        collection_id=collection_obj.collection_id
    )
    
    return collection_data


@router.post("/collections", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("collection.manage")),
    collection_in: CollectionCreate,
) -> CollectionResponse:
    """
    Tạo một bộ sưu tập sản phẩm mới (Dành cho Admin).
    """
    if collection_in.slug:
        existing = await collection_crud.get_by_slug(db=db, slug=collection_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection with this slug already exists"
            )
    
    collection = await collection_crud.create(db=db, obj_in=collection_in)
    
    await FastAPICache.clear(namespace="collections")
    
    return collection


@router.patch("/collections/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("collection.manage")),
    collection_id: int,
    collection_in: CollectionUpdate,
) -> CollectionResponse:
    """
    Cập nhật thông tin bộ sưu tập hiện có (Dành cho Admin).
    """
    collection = await collection_crud.get(db=db, id=collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    if collection_in.slug and collection_in.slug != collection.slug:
        existing = await collection_crud.get_by_slug(db=db, slug=collection_in.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection with this slug already exists"
            )
    
    updated_collection = await collection_crud.update(
        db=db,
        db_obj=collection,
        obj_in=collection_in
    )
    
    await FastAPICache.clear(namespace="collections")
    
    return updated_collection


@router.delete("/collections/{collection_id}", response_model=Message)
async def delete_collection(
    db: SessionDep,
    collection_id: int,
    current_user: User = Depends(require_permission("collection.manage")),
) -> Message:
    """
    Xóa vĩnh viễn một bộ sưu tập (Dành cho Admin).
    """
    collection = await collection_crud.get(db=db, id=collection_id)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    await collection_crud.delete(db=db, id=collection_id)
    
    await FastAPICache.clear(namespace="collections")
    
    return Message(message="Collection deleted successfully")


@router.post("/collections/{collection_id}/products", response_model=Message)
async def add_product_to_collection(
    db: SessionDep,
    collection_id: int,
    product_data: CollectionProductAdd,
    current_user: User = Depends(require_permission("collection.manage")),
) -> Message:
    """
    Thêm một sản phẩm vào bộ sưu tập hiện có.
    """
    collection = await collection_crud.get(db=db, id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    await collection_crud.add_product(
        db=db,
        collection_id=collection_id,
        product_id=product_data.product_id,
        display_order=product_data.display_order
    )
    
    await FastAPICache.clear(namespace="collections")
    
    return Message(message="Product added to collection successfully")


@router.delete("/collections/{collection_id}/products/{product_id}", response_model=Message)
async def remove_product_from_collection(
    db: SessionDep,
    collection_id: int,
    product_id: int,
    current_user: User = Depends(require_permission("collection.manage")),
) -> Message:
    """
    Xóa một sản phẩm ra khỏi bộ sưu tập.
    """
    success = await collection_crud.remove_product(
        db=db,
        collection_id=collection_id,
        product_id=product_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in collection"
        )
    
    await FastAPICache.clear(namespace="collections")
    
    return Message(message="Product removed from collection successfully")