from fastapi import APIRouter, Query, status, HTTPException, Depends
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from app.api.deps import (
    SessionDep,
    require_permission,
)
from app.crud.attribute import color as color_crud
from app.crud.attribute import size as size_crud
from app.models.common import Message
from app.models.user import User

router = APIRouter()


@router.get("/colors", response_model=list[dict])
@cache(expire=3600, namespace="attributes")
async def list_colors(
    db: SessionDep,
    is_active: bool = Query(True, description="Filter by active status"),
) -> list[dict]:
    """
    Lấy danh sách các màu sắc (Có lọc theo trạng thái hoạt động).
    """
    if is_active:
        colors = await color_crud.get_active(db=db)
    else:
        colors = await color_crud.get_multi(db=db, limit=100)
    
    return [
        {
            "color_id": c.color_id,
            "color_name": c.color_name,
            "color_code": c.color_code,
            "display_order": c.display_order,
            "is_active": c.is_active,
        }
        for c in colors
    ]


@router.get("/colors/{color_id}", response_model=dict)
async def get_color(
    db: SessionDep,
    color_id: int,
) -> dict:
    """
    Xem thông tin chi tiết của một màu sắc cụ thể.
    """
    color = await color_crud.get(db=db, id=color_id)
    
    if not color:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color not found"
        )
    
    return {
        "color_id": color.color_id,
        "color_name": color.color_name,
        "color_code": color.color_code,
        "display_order": color.display_order,
        "is_active": color.is_active,
    }


@router.post("/colors", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_color(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("attribute.manage")),
    color_name: str,
    color_code: str,
    display_order: int = 0,
    is_active: bool = True,
) -> dict:
    """
    Tạo một màu sắc mới (Dành cho Admin).
    """
    existing_name = await color_crud.get_by_name(db=db, name=color_name)
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Color name already exists"
        )
    
    existing_code = await color_crud.get_by_code(db=db, code=color_code)
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Color code already exists"
        )
    
    color = await color_crud.create(
        db=db,
        obj_in={
            "color_name": color_name,
            "color_code": color_code,
            "display_order": display_order,
            "is_active": is_active,
        }
    )

    await FastAPICache.clear(namespace="attributes")
    
    return {
        "color_id": color.color_id,
        "color_name": color.color_name,
        "color_code": color.color_code,
        "display_order": color.display_order,
        "is_active": color.is_active,
    }


@router.patch("/colors/{color_id}", response_model=dict)
async def update_color(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("attribute.manage")),
    color_id: int,
    color_name: str | None = None,
    color_code: str | None = None,
    display_order: int | None = None,
    is_active: bool | None = None,
) -> dict:
    """
    Cập nhật thông tin của một màu sắc (Dành cho Admin).
    """
    color = await color_crud.get(db=db, id=color_id)
    
    if not color:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color not found"
        )
    
    update_data = {}
    if color_name is not None:
        update_data["color_name"] = color_name
    if color_code is not None:
        update_data["color_code"] = color_code
    if display_order is not None:
        update_data["display_order"] = display_order
    if is_active is not None:
        update_data["is_active"] = is_active
    
    updated_color = await color_crud.update(
        db=db,
        db_obj=color,
        obj_in=update_data
    )

    await FastAPICache.clear(namespace="attributes")
    
    return {
        "color_id": updated_color.color_id,
        "color_name": updated_color.color_name,
        "color_code": updated_color.color_code,
        "display_order": updated_color.display_order,
        "is_active": updated_color.is_active,
    }


@router.delete("/colors/{color_id}", response_model=Message)
async def delete_color(
    db: SessionDep,
    color_id: int,
    current_user: User = Depends(require_permission("attribute.manage")),
) -> Message:
    """
    Xóa vĩnh viễn một màu sắc khỏi hệ thống (Dành cho Admin).
    """
    color = await color_crud.get(db=db, id=color_id)
    
    if not color:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color not found"
        )
    
    await color_crud.delete(db=db, id=color_id)

    await FastAPICache.clear(namespace="attributes")
    
    return Message(message="Color deleted successfully")


@router.get("/sizes", response_model=list[dict])
@cache(expire=3600, namespace="attributes")
async def list_sizes(
    db: SessionDep,
    size_type: str | None = Query(None, description="Filter by type (clothing, shoes, accessories)"),
    is_active: bool = Query(True, description="Filter by active status"),
) -> list[dict]:
    """
    Lấy danh sách các kích thước (Có lọc theo loại và trạng thái).
    """
    sizes = await size_crud.get_active(db=db, size_type=size_type)
    
    return [
        {
            "size_id": s.size_id,
            "size_name": s.size_name,
            "size_type": s.size_type,
            "display_order": s.display_order,
            "is_active": s.is_active,
        }
        for s in sizes
    ]


@router.get("/sizes/{size_id}", response_model=dict)
async def get_size(
    db: SessionDep,
    size_id: int,
) -> dict:
    """
    Xem thông tin chi tiết của một kích thước cụ thể.
    """
    size = await size_crud.get(db=db, id=size_id)
    
    if not size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Size not found"
        )
    
    return {
        "size_id": size.size_id,
        "size_name": size.size_name,
        "size_type": size.size_type,
        "display_order": size.display_order,
        "is_active": size.is_active,
    }


@router.post("/sizes", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_size(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("attribute.manage")),
    size_name: str,
    size_type: str = "clothing",
    display_order: int = 0,
    is_active: bool = True,
) -> dict:
    """
    Tạo một kích thước mới (Dành cho Admin).
    """
    existing = await size_crud.get_by_name(db=db, name=size_name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Size name already exists"
        )
    
    size = await size_crud.create(
        db=db,
        obj_in={
            "size_name": size_name,
            "size_type": size_type,
            "display_order": display_order,
            "is_active": is_active,
        }
    )

    await FastAPICache.clear(namespace="attributes")
    
    return {
        "size_id": size.size_id,
        "size_name": size.size_name,
        "size_type": size.size_type,
        "display_order": size.display_order,
        "is_active": size.is_active,
    }


@router.patch("/sizes/{size_id}", response_model=dict)
async def update_size(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("attribute.manage")),
    size_id: int,
    size_name: str | None = None,
    size_type: str | None = None,
    display_order: int | None = None,
    is_active: bool | None = None,
) -> dict:
    """
    Cập nhật thông tin của một kích thước (Dành cho Admin).
    """
    size = await size_crud.get(db=db, id=size_id)
    
    if not size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Size not found"
        )
    
    update_data = {}
    if size_name is not None:
        update_data["size_name"] = size_name
    if size_type is not None:
        update_data["size_type"] = size_type
    if display_order is not None:
        update_data["display_order"] = display_order
    if is_active is not None:
        update_data["is_active"] = is_active
    
    updated_size = await size_crud.update(
        db=db,
        db_obj=size,
        obj_in=update_data
    )

    await FastAPICache.clear(namespace="attributes")
    
    return {
        "size_id": updated_size.size_id,
        "size_name": updated_size.size_name,
        "size_type": updated_size.size_type,
        "display_order": updated_size.display_order,
        "is_active": updated_size.is_active,
    }


@router.delete("/sizes/{size_id}", response_model=Message)
async def delete_size(
    db: SessionDep,
    size_id: int,
    current_user: User = Depends(require_permission("attribute.manage")),
) -> Message:
    """
    Xóa vĩnh viễn một kích thước khỏi hệ thống (Dành cho Admin).
    """
    size = await size_crud.get(db=db, id=size_id)
    
    if not size:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Size not found"
        )
    
    await size_crud.delete(db=db, id=size_id)

    await FastAPICache.clear(namespace="attributes")
    
    return Message(message="Size deleted successfully")