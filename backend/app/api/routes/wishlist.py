from fastapi import APIRouter, Query, status, HTTPException
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    CurrentUser,
)
from app.crud.wishlist import wishlist as wishlist_crud
from app.crud.wishlist import wishlist_item as wishlist_item_crud
from app.models.wishlist import (
    WishlistResponse,
    WishlistDetailResponse,
    WishlistCreate,
    WishlistUpdate,
    WishlistItemCreate,
    WishlistItemUpdate,
    WishlistItemMove,
)
from app.models.common import Message

router = APIRouter()


def wishlist_key_builder(func, namespace: str = "", *args, **kwargs):
    current_user = kwargs.get("current_user") or kwargs.get("kwargs", {}).get("current_user")
    
    key = f"wishlist:user:{current_user.user_id}:{func.__name__}"
    
    wishlist_id = kwargs.get("wishlist_id") or kwargs.get("kwargs", {}).get("wishlist_id")
    if wishlist_id:
        key += f":{wishlist_id}"
        
    return key

async def clear_user_wishlist_cache(user_id: int):
    try:
        redis = FastAPICache.get_backend().redis
        keys = await redis.keys(f"wishlist:user:{user_id}:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        print(f"Cache clear error: {e}")

@router.get("/me", response_model=list[WishlistResponse])
@cache(expire=300, namespace="wishlists", key_builder=wishlist_key_builder)
async def get_my_wishlists(
    db: SessionDep,
    current_user: CurrentUser,
) -> list[WishlistResponse]:
    """
    Lấy danh sách tất cả các wishlist của người dùng hiện tại.
    """
    wishlists = await wishlist_crud.get_by_user(
        db=db,
        user_id=current_user.user_id,
        load_items=False
    )
    
    response_wishlists = []
    for wishlist in wishlists:
        items = await wishlist_item_crud.get_by_wishlist(
            db=db,
            wishlist_id=wishlist.wishlist_id
        )
        response_wishlist = WishlistResponse(
            wishlist_id=wishlist.wishlist_id,
            user_id=wishlist.user_id,
            name=wishlist.name,
            is_default=wishlist.is_default,
            description=wishlist.description,
            created_at=wishlist.created_at,
            updated_at=wishlist.updated_at,
            item_count=len(items)
        )
        response_wishlists.append(response_wishlist)
    
    return response_wishlists


@router.get("/me/default", response_model=WishlistDetailResponse)
@cache(expire=300, namespace="wishlists", key_builder=wishlist_key_builder)
async def get_default_wishlist(
    db: SessionDep,
    current_user: CurrentUser,
) -> WishlistDetailResponse:
    """
    Truy vấn thông tin chi tiết của wishlist được thiết lập làm mặc định.
    """
    wishlist = await wishlist_crud.get_or_create_default(
        db=db,
        user_id=current_user.user_id
    )
    
    items = await wishlist_item_crud.get_by_wishlist(
        db=db,
        wishlist_id=wishlist.wishlist_id
    )
    
    return WishlistDetailResponse(
        wishlist_id=wishlist.wishlist_id,
        user_id=wishlist.user_id,
        name=wishlist.name,
        is_default=wishlist.is_default,
        description=wishlist.description,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        item_count=len(items),
        items=items
    )


@router.post("", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
async def create_wishlist(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    wishlist_in: WishlistCreate,
) -> WishlistResponse:
    """
    Tạo một wishlist mới cho người dùng.
    """
    wishlist = await wishlist_crud.create_for_user(
        db=db,
        user_id=current_user.user_id,
        obj_in=wishlist_in
    )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    return WishlistResponse(
        wishlist_id=wishlist.wishlist_id,
        user_id=wishlist.user_id,
        name=wishlist.name,
        is_default=wishlist.is_default,
        description=wishlist.description,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        item_count=0
    )


@router.get("/check/{product_id}", response_model=dict)
@cache(expire=180, namespace="wishlists", key_builder=wishlist_key_builder)
async def check_in_wishlist(
    db: SessionDep,
    current_user: CurrentUser,
    product_id: int,
    variant_id: int | None = Query(None, description="Variant ID"),
) -> dict:
    """
    Kiểm tra xem một sản phẩm (hoặc biến thể) cụ thể đã có trong danh sách yêu thích chưa.
    """
    in_wishlist = await wishlist_item_crud.check_in_wishlist(
        db=db,
        user_id=current_user.user_id,
        product_id=product_id,
        variant_id=variant_id
    )
    
    return {"in_wishlist": in_wishlist}


@router.get("/{wishlist_id}", response_model=WishlistDetailResponse)
@cache(expire=300, namespace="wishlists", key_builder=wishlist_key_builder)
async def get_wishlist(
    db: SessionDep,
    current_user: CurrentUser,
    wishlist_id: int,
) -> WishlistDetailResponse:
    """
    Xem thông tin chi tiết và toàn bộ sản phẩm bên trong một wishlist cụ thể.
    """
    wishlist = await wishlist_crud.get(db=db, id=wishlist_id)
    
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    
    if wishlist.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this wishlist"
        )
    
    items = await wishlist_item_crud.get_by_wishlist(
        db=db,
        wishlist_id=wishlist_id
    )
    
    return WishlistDetailResponse(
        wishlist_id=wishlist.wishlist_id,
        user_id=wishlist.user_id,
        name=wishlist.name,
        is_default=wishlist.is_default,
        description=wishlist.description,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        item_count=len(items),
        items=items
    )


@router.patch("/{wishlist_id}", response_model=WishlistResponse)
async def update_wishlist(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    wishlist_id: int,
    wishlist_in: WishlistUpdate,
) -> WishlistResponse:
    """
    Cập nhật thông tin cơ bản (tên, mô tả) của một wishlist.
    """
    wishlist = await wishlist_crud.get(db=db, id=wishlist_id)
    
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    
    if wishlist.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this wishlist"
        )
    
    updated_wishlist = await wishlist_crud.update(
        db=db,
        db_obj=wishlist,
        obj_in=wishlist_in
    )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    items = await wishlist_item_crud.get_by_wishlist(
        db=db,
        wishlist_id=updated_wishlist.wishlist_id
    )
    
    return WishlistResponse(
        wishlist_id=updated_wishlist.wishlist_id,
        user_id=updated_wishlist.user_id,
        name=updated_wishlist.name,
        is_default=updated_wishlist.is_default,
        description=updated_wishlist.description,
        created_at=updated_wishlist.created_at,
        updated_at=updated_wishlist.updated_at,
        item_count=len(items)
    )


@router.delete("/{wishlist_id}", response_model=Message)
async def delete_wishlist(
    db: SessionDep,
    current_user: CurrentUser,
    wishlist_id: int,
) -> Message:
    """
    Xóa vĩnh viễn một wishlist (Không áp dụng cho wishlist mặc định).
    """
    wishlist = await wishlist_crud.get(db=db, id=wishlist_id)
    
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    
    if wishlist.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this wishlist"
        )
    
    if wishlist.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default wishlist"
        )
    
    await wishlist_crud.delete_user_wishlist(
        db=db,
        wishlist_id=wishlist_id,
        user_id=current_user.user_id
    )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    return Message(message="Wishlist deleted successfully")


@router.post("/{wishlist_id}/set-default", response_model=WishlistResponse)
async def set_default_wishlist(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    wishlist_id: int,
) -> WishlistResponse:
    """
    Thiết lập một wishlist cụ thể làm danh sách yêu thích mặc định.
    """
    try:
        wishlist = await wishlist_crud.set_default(
            db=db,
            wishlist_id=wishlist_id,
            user_id=current_user.user_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    items = await wishlist_item_crud.get_by_wishlist(
        db=db,
        wishlist_id=wishlist.wishlist_id
    )
    
    return WishlistResponse(
        wishlist_id=wishlist.wishlist_id,
        user_id=wishlist.user_id,
        name=wishlist.name,
        is_default=wishlist.is_default,
        description=wishlist.description,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        item_count=len(items)
    )


@router.post("/{wishlist_id}/items", response_model=WishlistDetailResponse, status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    wishlist_id: int,
    item_in: WishlistItemCreate,
) -> WishlistDetailResponse:
    """
    Thêm một sản phẩm mới vào wishlist được chỉ định.
    """
    wishlist = await wishlist_crud.get(db=db, id=wishlist_id)
    
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )
    
    if wishlist.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add to this wishlist"
        )
    
    await wishlist_item_crud.add_item(
        db=db,
        wishlist_id=wishlist_id,
        product_id=item_in.product_id,
        variant_id=item_in.variant_id,
        note=item_in.note
    )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    wishlist = await wishlist_crud.get(db=db, id=wishlist_id)
    items = await wishlist_item_crud.get_by_wishlist(
        db=db,
        wishlist_id=wishlist_id
    )
    
    return WishlistDetailResponse(
        wishlist_id=wishlist.wishlist_id,
        user_id=wishlist.user_id,
        name=wishlist.name,
        is_default=wishlist.is_default,
        description=wishlist.description,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        item_count=len(items),
        items=items
    )


@router.post("/add-to-default", response_model=WishlistDetailResponse)
async def add_to_default_wishlist(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    item_in: WishlistItemCreate,
) -> WishlistDetailResponse:
    """
    Thêm sản phẩm trực tiếp vào wishlist mặc định của người dùng.
    """
    wishlist = await wishlist_crud.get_or_create_default(
        db=db,
        user_id=current_user.user_id
    )
    
    await wishlist_item_crud.add_item(
        db=db,
        wishlist_id=wishlist.wishlist_id,
        product_id=item_in.product_id,
        variant_id=item_in.variant_id,
        note=item_in.note
    )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    wishlist = await wishlist_crud.get_or_create_default(
        db=db,
        user_id=current_user.user_id
    )
    items = await wishlist_item_crud.get_by_wishlist(
        db=db,
        wishlist_id=wishlist.wishlist_id
    )
    
    return WishlistDetailResponse(
        wishlist_id=wishlist.wishlist_id,
        user_id=wishlist.user_id,
        name=wishlist.name,
        is_default=wishlist.is_default,
        description=wishlist.description,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        item_count=len(items),
        items=items
    )


@router.patch("/items/{item_id}", response_model=WishlistDetailResponse)
async def update_wishlist_item(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    item_id: int,
    item_in: WishlistItemUpdate,
) -> WishlistDetailResponse:
    """
    Cập nhật các thông tin phụ trợ (như ghi chú) cho một mặt hàng trong wishlist.
    """
    item = await wishlist_item_crud.get(db=db, id=item_id)
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    wishlist = await wishlist_crud.get(db=db, id=item.wishlist_id)
    if not wishlist or wishlist.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this item"
        )
    
    updated_item = await wishlist_item_crud.update(
        db=db,
        db_obj=item,
        obj_in=item_in
    )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    items = await wishlist_item_crud.get_by_wishlist(
        db=db,
        wishlist_id=wishlist.wishlist_id
    )
    
    return WishlistDetailResponse(
        wishlist_id=wishlist.wishlist_id,
        user_id=wishlist.user_id,
        name=wishlist.name,
        is_default=wishlist.is_default,
        description=wishlist.description,
        created_at=wishlist.created_at,
        updated_at=wishlist.updated_at,
        item_count=len(items),
        items=items
    )


@router.delete("/items/{item_id}", response_model=Message)
async def remove_from_wishlist(
    db: SessionDep,
    current_user: CurrentUser,
    item_id: int,
) -> Message:
    """
    Xóa một sản phẩm ra khỏi danh sách yêu thích.
    """
    result = await wishlist_item_crud.remove_item(
        db=db,
        wishlist_item_id=item_id,
        user_id=current_user.user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    return Message(message="Item removed from wishlist successfully")


@router.post("/items/{item_id}/move", response_model=Message)
async def move_wishlist_item(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    item_id: int,
    move_data: WishlistItemMove,
) -> Message:
    """
    Di chuyển một sản phẩm từ wishlist này sang wishlist khác của cùng một người dùng.
    """
    result = await wishlist_item_crud.move_to_wishlist(
        db=db,
        item_id=item_id,
        target_wishlist_id=move_data.target_wishlist_id,
        user_id=current_user.user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item or target wishlist not found"
        )
    
    await clear_user_wishlist_cache(current_user.user_id)
    
    return Message(message="Item moved successfully")