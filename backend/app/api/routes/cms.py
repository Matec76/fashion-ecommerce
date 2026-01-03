from fastapi import APIRouter, Query, status, HTTPException, UploadFile, File, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.core.config import settings
from app.core.storage import S3Storage
from app.api.deps import (
    SessionDep,
    require_permission,
)
from app.models.user import User
from app.crud.cms import banner_slide as banner_crud
from app.crud.cms import page as page_crud
from app.crud.cms import menu as menu_crud
from app.crud.cms import menu_item as menu_item_crud
from app.models.cms import (
    BannerSlideResponse,
    BannerSlideCreate,
    BannerSlideUpdate,
    PageResponse,
    PageCreate,
    PageUpdate,
    MenuResponse,
    MenuCreate,
    MenuUpdate,
    MenuItemResponse,
    MenuItemCreate,
    MenuItemUpdate,
)
from app.models.common import Message
from app.services.mongo_service import mongo_service 

router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_cms_file(
    current_user: User = Depends(require_permission("cms.manage")),
    file: UploadFile = File(...),
):
    """
    Tải lên tệp tin hình ảnh cho hệ thống CMS (Banner, bài viết) lên S3.
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
        folder = settings.S3_BANNERS_FOLDER
        result = await S3Storage.upload_file(
            file=file.file,
            filename=file.filename,
            folder=folder,
            content_type=file.content_type,
        )

        final_url = result.get("cdn_url") or result["file_url"]

        return {"url": final_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload: {str(e)}")



@router.get("/banners", response_model=list[BannerSlideResponse])
@cache(expire=300, namespace="cms-banners")
async def list_banners(
    db: SessionDep,
    is_active: bool = Query(True, description="Filter by active status"),
) -> list[BannerSlideResponse]:
    """
    Lấy danh sách các banner slide (Có lọc theo trạng thái hoạt động).
    """
    if is_active:
        banners = await banner_crud.get_active(db=db, limit=20)
    else:
        banners = await banner_crud.get_multi(db=db, limit=100)
    return banners


@router.get("/banners/{banner_id}", response_model=BannerSlideResponse)
@cache(expire=300, namespace="cms-banners")
async def get_banner(
    db: SessionDep,
    banner_id: int,
) -> BannerSlideResponse:
    """
    Xem thông tin chi tiết của một banner cụ thể.
    """
    banner = await banner_crud.get(db=db, id=banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return banner


@router.post("/banners", response_model=BannerSlideResponse, status_code=status.HTTP_201_CREATED)
async def create_banner(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    banner_in: BannerSlideCreate,
) -> BannerSlideResponse:
    """
    Tạo một banner slide mới (Yêu cầu quyền cms.manage).
    """
    banner = await banner_crud.create(db=db, obj_in=banner_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "CREATE_BANNER",
        "target_id": banner.banner_id,
        "details": f"Admin {current_user.email} đã tạo banner mới: {banner.title}"
    })

    await FastAPICache.clear(namespace="cms-banners")
    return banner


@router.patch("/banners/{banner_id}", response_model=BannerSlideResponse)
async def update_banner(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    banner_id: int,
    banner_in: BannerSlideUpdate,
) -> BannerSlideResponse:
    """
    Cập nhật thông tin của một banner slide hiện có.
    """
    banner = await banner_crud.get(db=db, id=banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    updated_banner = await banner_crud.update(db=db, db_obj=banner, obj_in=banner_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "UPDATE_BANNER",
        "target_id": banner_id,
        "details": f"Admin {current_user.email} đã cập nhật banner ID {banner_id}"
    })

    await FastAPICache.clear(namespace="cms-banners")
    return updated_banner


@router.delete("/banners/{banner_id}", response_model=Message)
async def delete_banner(
    db: SessionDep,
    banner_id: int,
    current_user: User = Depends(require_permission("cms.manage")),
) -> Message:
    """
    Xóa một banner slide khỏi hệ thống.
    """
    banner = await banner_crud.get(db=db, id=banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    
    await banner_crud.delete(db=db, id=banner_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_BANNER",
        "target_id": banner_id,
        "details": f"Admin {current_user.email} đã xóa banner ID {banner_id}"
    })

    await FastAPICache.clear(namespace="cms-banners")
    return Message(message="Banner deleted successfully")


@router.post("/banners/reorder", response_model=list[BannerSlideResponse])
async def reorder_banners(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    banner_orders: dict[int, int],
) -> list[BannerSlideResponse]:
    """
    Thay đổi thứ tự hiển thị của các banner slide.
    """
    banners = await banner_crud.reorder(db=db, banner_orders=banner_orders)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "REORDER_BANNERS",
        "details": f"Admin {current_user.email} đã thay đổi thứ tự hiển thị của các banner."
    })

    await FastAPICache.clear(namespace="cms-banners")
    return banners


@router.get("/pages/search", response_model=list[PageResponse])
@cache(expire=300, namespace="cms-pages")
async def search_pages(
    db: SessionDep,
    q: str = Query(..., min_length=2, description="Search query"),
    published_only: bool = Query(True),
) -> list[PageResponse]:
    """
    Tìm kiếm các trang hoặc bài viết CMS theo từ khóa.
    """
    return await page_crud.search(db=db, query=q, published_only=published_only, limit=50)


@router.get("/pages", response_model=list[PageResponse])
@cache(expire=1800, namespace="cms-pages")
async def list_pages(
    db: SessionDep,
    published_only: bool = Query(True),
) -> list[PageResponse]:
    """
    Lấy danh sách các trang bài viết (Có tùy chọn chỉ lấy bài đã xuất bản).
    """
    if published_only:
        return await page_crud.get_published(db=db, limit=100)
    return await page_crud.get_multi(db=db, limit=100)


@router.get("/pages/slug/{slug}", response_model=PageResponse)
@cache(expire=3600, namespace="cms-pages")
async def get_page_by_slug(db: SessionDep, slug: str) -> PageResponse:
    """
    Lấy thông tin trang bài viết dựa trên đường dẫn slug.
    """
    page = await page_crud.get_by_slug(db=db, slug=slug)
    if not page or not page.is_published:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.get("/pages/{page_id}", response_model=PageResponse)
@cache(expire=1800, namespace="cms-pages")
async def get_page(db: SessionDep, page_id: int) -> PageResponse:
    """
    Xem thông tin chi tiết của một trang bài viết theo ID.
    """
    page = await page_crud.get(db=db, id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.post("/pages", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    page_in: PageCreate,
) -> PageResponse:
    """
    Tạo một trang nội dung hoặc bài viết mới.
    """
    if page_in.slug:
        existing = await page_crud.get_by_slug(db=db, slug=page_in.slug)
        if existing:
            raise HTTPException(status_code=400, detail="Page slug already exists")
    
    page = await page_crud.create(db=db, obj_in=page_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "CREATE_PAGE",
        "target_id": page.page_id,
        "details": f"Admin {current_user.email} đã tạo trang/bài viết mới: {page.title}"
    })

    await FastAPICache.clear(namespace="cms-pages")
    return page


@router.patch("/pages/{page_id}", response_model=PageResponse)
async def update_page(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    page_id: int,
    page_in: PageUpdate,
) -> PageResponse:
    """
    Cập nhật nội dung của một trang bài viết hiện có.
    """
    page = await page_crud.get(db=db, id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page_in.slug and page_in.slug != page.slug:
        existing = await page_crud.get_by_slug(db=db, slug=page_in.slug)
        if existing:
            raise HTTPException(status_code=400, detail="Page slug already exists")
    
    updated_page = await page_crud.update(db=db, db_obj=page, obj_in=page_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "UPDATE_PAGE",
        "target_id": page_id,
        "details": f"Admin {current_user.email} đã chỉnh sửa trang ID {page_id}"
    })

    await FastAPICache.clear(namespace="cms-pages")
    return updated_page


@router.delete("/pages/{page_id}", response_model=Message)
async def delete_page(
    db: SessionDep,
    page_id: int,
    current_user: User = Depends(require_permission("cms.manage")),
) -> Message:
    """
    Xóa một trang bài viết khỏi hệ thống.
    """
    page = await page_crud.get(db=db, id=page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    await page_crud.delete(db=db, id=page_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_PAGE",
        "target_id": page_id,
        "details": f"Admin {current_user.email} đã xóa trang/bài viết ID {page_id}."
    })

    await FastAPICache.clear(namespace="cms-pages")
    return Message(message="Page deleted successfully")


@router.post("/pages/{page_id}/publish", response_model=PageResponse)
async def publish_page(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    page_id: int,
) -> PageResponse:
    """
    Công khai (xuất bản) một trang bài viết để người dùng có thể xem.
    """
    page = await page_crud.publish(db=db, page_id=page_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "PUBLISH_PAGE",
        "target_id": page_id,
        "details": f"Admin {current_user.email} đã công khai trang ID {page_id}."
    })

    await FastAPICache.clear(namespace="cms-pages")
    return page


@router.post("/pages/{page_id}/unpublish", response_model=PageResponse)
async def unpublish_page(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    page_id: int,
) -> PageResponse:
    """
    Gỡ bỏ trạng thái xuất bản của một trang bài viết.
    """
    page = await page_crud.unpublish(db=db, page_id=page_id)
    await FastAPICache.clear(namespace="cms-pages")
    return page



@router.get("/menus", response_model=list[MenuResponse])
@cache(expire=3600, namespace="cms-menus")
async def list_menus(db: SessionDep) -> list[MenuResponse]:
    """
    Lấy danh sách tất cả các menu điều hướng đang hoạt động.
    """
    return await menu_crud.get_active(db=db)


@router.get("/menus/location/{location}", response_model=MenuResponse)
@cache(expire=3600, namespace="cms-menus")
async def get_menu_by_location(db: SessionDep, location: str) -> MenuResponse:
    """
    Lấy thông tin menu dựa trên vị trí hiển thị (Ví dụ: header, footer).
    """
    menu = await menu_crud.get_by_location(db=db, location=location)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


@router.get("/menus/{menu_id}", response_model=MenuResponse)
@cache(expire=3600, namespace="cms-menus")
async def get_menu(db: SessionDep, menu_id: int) -> MenuResponse:
    """
    Xem chi tiết một menu và tất cả các mục menu trực thuộc.
    """
    menu = await menu_crud.get_with_items(db=db, menu_id=menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    return menu


@router.get("/menus/{menu_id}/tree", response_model=list[dict])
@cache(expire=7200, namespace="cms-menus")
async def get_menu_tree(
    db: SessionDep,
    menu_id: int,
    active_only: bool = Query(True),
) -> list[dict]:
    """
    Lấy cấu trúc phân cấp cây của menu theo ID.
    """
    return await menu_item_crud.get_tree(db=db, menu_id=menu_id, active_only=active_only)


@router.post("/menus", response_model=MenuResponse, status_code=status.HTTP_201_CREATED)
async def create_menu(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    menu_in: MenuCreate,
) -> MenuResponse:
    """
    Tạo một menu mới tại một vị trí hiển thị cụ thể.
    """
    menu = await menu_crud.create(db=db, obj_in=menu_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "CREATE_MENU",
        "target_id": menu.menu_id,
        "details": f"Admin {current_user.email} đã tạo menu mới tại vị trí: {menu.location}"
    })

    await FastAPICache.clear(namespace="cms-menus")
    return menu


@router.patch("/menus/{menu_id}", response_model=MenuResponse)
async def update_menu(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    menu_id: int,
    menu_in: MenuUpdate,
) -> MenuResponse:
    """
    Cập nhật thông tin cấu hình của một menu.
    """
    menu = await menu_crud.get(db=db, id=menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    updated_menu = await menu_crud.update(db=db, db_obj=menu, obj_in=menu_in)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "UPDATE_MENU",
        "target_id": menu_id,
        "details": f"Admin {current_user.email} cập nhật Menu ID {menu_id}: {menu_in.model_dump(exclude_unset=True)}"
    })

    await FastAPICache.clear(namespace="cms-menus")
    return updated_menu


@router.delete("/menus/{menu_id}", response_model=Message)
async def delete_menu(
    db: SessionDep,
    menu_id: int,
    current_user: User = Depends(require_permission("cms.manage")),
) -> Message:
    """
    Xóa một menu khỏi hệ thống.
    """
    menu = await menu_crud.get(db=db, id=menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu not found")
    
    await menu_crud.delete(db=db, id=menu_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_MENU_ITEM",
        "target_id": menu_id,
        "details": f"Admin {current_user.email} đã xóa mục menu ID {menu_id}."
    })

    await FastAPICache.clear(namespace="cms-menus")
    return Message(message="Menu deleted successfully")



@router.get("/menu-items/{menu_id}", response_model=list[MenuItemResponse])
async def list_menu_items(
    db: SessionDep,
    menu_id: int,
    parent_id: int | None = Query(None),
) -> list[MenuItemResponse]:
    """
    Liệt kê các mục menu thuộc một menu cụ thể (Có lọc theo mục cha).
    """
    return await menu_item_crud.get_by_menu(db=db, menu_id=menu_id, parent_id=parent_id)


@router.post("/menu-items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    item_in: MenuItemCreate,
) -> MenuItemResponse:
    """
    Tạo một mục menu mới.
    """
    item = await menu_item_crud.create(db=db, obj_in=item_in)
    await FastAPICache.clear(namespace="cms-menus")
    return item


@router.patch("/menu-items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    item_id: int,
    item_in: MenuItemUpdate,
) -> MenuItemResponse:
    """
    Cập nhật thông tin và đường dẫn của một mục menu.
    """
    item = await menu_item_crud.get(db=db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    updated_item = await menu_item_crud.update(db=db, db_obj=item, obj_in=item_in)
    await FastAPICache.clear(namespace="cms-menus")
    return updated_item


@router.delete("/menu-items/{item_id}", response_model=Message)
async def delete_menu_item(
    db: SessionDep,
    item_id: int,
    current_user: User = Depends(require_permission("cms.manage")),
) -> Message:
    """
    Xóa một mục menu khỏi danh sách điều hướng.
    """
    item = await menu_item_crud.get(db=db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    await menu_item_crud.delete(db=db, id=item_id)
    await FastAPICache.clear(namespace="cms-menus")
    return Message(message="Menu item deleted successfully")


@router.post("/menu-items/reorder", response_model=list[MenuItemResponse])
async def reorder_menu_items(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    item_orders: dict[int, int],
) -> list[MenuItemResponse]:
    """
    Sắp xếp lại thứ tự hiển thị của các mục menu.
    """
    items = await menu_item_crud.reorder(db=db, item_orders=item_orders)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "REORDER_MENU_ITEMS",
        "details": f"Admin {current_user.email} đã sắp xếp lại thứ tự các mục menu."
    })

    await FastAPICache.clear(namespace="cms-menus")
    return items


@router.post("/menu-items/{item_id}/move", response_model=MenuItemResponse)
async def move_menu_item(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("cms.manage")),
    item_id: int,
    new_parent_id: int | None = Query(None),
) -> MenuItemResponse:
    """
    Di chuyển mục menu sang một mục cha mới hoặc ra ngoài cấp gốc.
    """
    item = await menu_item_crud.move_item(db=db, item_id=item_id, new_parent_id=new_parent_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "MOVE_MENU_ITEM",
        "target_id": item_id,
        "details": f"Admin {current_user.email} đã di chuyển mục menu ID {item_id} sang cha mới ID {new_parent_id}."
    })

    await FastAPICache.clear(namespace="cms-menus")
    return item