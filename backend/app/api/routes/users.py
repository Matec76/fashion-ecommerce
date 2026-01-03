from fastapi import APIRouter, Query, status, HTTPException, Response, Depends, UploadFile, File
from fastapi_cache.decorator import cache
from fastapi_cache import FastAPICache

from app.api.deps import (
    SessionDep,
    CurrentUser,
    PaginationDep,
    require_permission,
)
from app.crud.user import user as user_crud
from app.crud.address import address as address_crud
from app.crud.role import role as role_crud
from app.models.user import (
    User,
    UserResponse,
    UserDetailResponse,
    UserCreate,
    UserUpdate,
    UserUpdateMe,
    AddressResponse,
    AddressCreate,
    AddressUpdate,
)
from app.models.common import Message
from app.core.config import settings
from app.core.storage import S3Storage
from app.services.mongo_service import mongo_service

router = APIRouter()



def user_profile_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho profile người dùng.
    """
    view_kwargs = kwargs.get("kwargs", {})
    current_user = view_kwargs.get("current_user") or kwargs.get("current_user")
    
    user_id = current_user.user_id if current_user else "anonymous"
    return f"user:{user_id}:profile"


def user_addresses_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho danh sách địa chỉ.
    """
    view_kwargs = kwargs.get("kwargs", {})
    current_user = view_kwargs.get("current_user") or kwargs.get("current_user")
    
    if not current_user:
        return "user:anonymous:addresses"
    return f"user:{current_user.user_id}:addresses"


def specific_address_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho một địa chỉ cụ thể.
    """
    view_kwargs = kwargs.get("kwargs", {})
    current_user = view_kwargs.get("current_user") or kwargs.get("current_user")
    address_id = view_kwargs.get("address_id") or kwargs.get("address_id")
    
    if not current_user:
        return f"user:anonymous:address:{address_id}"
        
    return f"user:{current_user.user_id}:address:{address_id}"


def admin_user_detail_key_builder(func, namespace: str = "", *args, **kwargs):
    """
    Tạo key cache cho Admin khi xem chi tiết user khác.
    """
    view_kwargs = kwargs.get("kwargs", {})
    user_id = view_kwargs.get("user_id") or kwargs.get("user_id")
    return f"admin:user:{user_id}"



async def invalidate_user_profile(user_id: int):
    """Xóa cache profile của user."""
    key = f"user:{user_id}:profile"
    try:
        await FastAPICache.get_backend().redis.delete(key)
    except Exception as e:
        print(f"Lỗi xóa cache key {key}: {e}")


async def invalidate_user_addresses(user_id: int):
    """Xóa cache danh sách địa chỉ của user."""
    key = f"user:{user_id}:addresses"
    try:
        await FastAPICache.get_backend().redis.delete(key)
    except Exception as e:
        print(f"Lỗi xóa cache key {key}: {e}")


async def invalidate_specific_address(user_id: int, address_id: int):
    """Xóa cache của một địa chỉ cụ thể."""
    key = f"user:{user_id}:address:{address_id}"
    try:
        await FastAPICache.get_backend().redis.delete(key)
    except Exception as e:
        print(f"Lỗi xóa cache key {key}: {e}")


async def invalidate_admin_user_view(user_id: int):
    """Xóa cache view user của Admin."""
    key = f"admin:user:{user_id}"
    try:
        await FastAPICache.get_backend().redis.delete(key)
    except Exception as e:
        print(f"Lỗi xóa cache key {key}: {e}")


async def invalidate_all_user_caches(user_id: int):
    """Xóa tất cả các loại cache liên quan đến một user."""
    await invalidate_user_profile(user_id)
    await invalidate_user_addresses(user_id)
    await invalidate_admin_user_view(user_id)




@router.get("/me", response_model=UserDetailResponse)
@cache(expire=300, key_builder=user_profile_key_builder)
async def get_current_user(
    db: SessionDep,
    current_user: CurrentUser,
) -> UserDetailResponse:
    """
    Lấy thông tin chi tiết hồ sơ của người dùng hiện tại.
    """
    user_with_role = await user_crud.get_multi_with_role(
        db=db,
        filters={"user_id": current_user.user_id},
        limit=1
    )
    
    if user_with_role:
        return user_with_role[0]
    
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    user_in: UserUpdateMe,
) -> UserResponse:
    """
    Cập nhật thông tin cá nhân của người dùng hiện tại.
    """
    updated_user = await user_crud.update(
        db=db,
        db_obj=current_user,
        obj_in=user_in
    )
    
    await invalidate_user_profile(current_user.user_id)
    await invalidate_admin_user_view(current_user.user_id)
    
    return updated_user


@router.put("/me/avatar", response_model=UserResponse)
async def update_my_avatar(
    db: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> UserResponse:
    """
    Upload và cập nhật Avatar cho user hiện tại (Sử dụng S3).
    """
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Định dạng file không hợp lệ. Chỉ chấp nhận: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        limit_mb = settings.MAX_UPLOAD_SIZE / 1024 / 1024
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"File quá lớn. Tối đa cho phép: {int(limit_mb)}MB"
        )

    try:
        result = await S3Storage.upload_file(
            file=file.file,
            filename=file.filename,
            folder=settings.S3_USER_AVATARS_FOLDER,
            content_type=file.content_type,
        )
        new_avatar_url = result.get("cdn_url") or result["file_url"]

        updated_user = await user_crud.update(
            db=db, 
            db_obj=current_user, 
            obj_in={"avatar_url": new_avatar_url} 
        )
        
        await invalidate_user_profile(current_user.user_id)
        await invalidate_admin_user_view(current_user.user_id)

        return updated_user

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi upload avatar: {str(e)}")


@router.delete("/me", response_model=Message)
async def delete_current_user(
    *,
    db: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """
    Người dùng tự xóa tài khoản của mình (Xóa mềm).
    """
    await user_crud.delete(db=db, id=current_user.user_id, soft_delete=True)
    await invalidate_all_user_caches(current_user.user_id)
    
    return Message(message="Xóa tài khoản thành công")



@router.get("/me/addresses", response_model=list[AddressResponse])
@cache(expire=300, key_builder=user_addresses_key_builder)
async def get_current_user_addresses(
    db: SessionDep,
    current_user: CurrentUser,
) -> list[AddressResponse]:
    """
    Lấy danh sách tất cả địa chỉ của người dùng hiện tại.
    """
    addresses = await address_crud.get_by_user(
        db=db,
        user_id=current_user.user_id
    )
    return addresses


@router.post("/me/addresses", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_in: AddressCreate,
) -> AddressResponse:
    """
    Thêm mới một địa chỉ giao hàng.
    """
    address = await address_crud.create_for_user(
        db=db,
        user_id=current_user.user_id,
        obj_in=address_in
    )
    
    await invalidate_user_addresses(current_user.user_id)
    
    return address


@router.get("/me/addresses/{address_id}", response_model=AddressResponse)
@cache(expire=300, key_builder=specific_address_key_builder)
async def get_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
) -> AddressResponse:
    """
    Xem chi tiết một địa chỉ cụ thể.
    """
    address = await address_crud.get(db=db, id=address_id)
    
    if not address or address.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa chỉ"
        )
    
    return address


@router.patch("/me/addresses/{address_id}", response_model=AddressResponse)
async def update_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
    address_in: AddressUpdate,
) -> AddressResponse:
    """
    Cập nhật thông tin địa chỉ.
    """
    address = await address_crud.get(db=db, id=address_id)
    
    if not address or address.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa chỉ"
        )
    
    updated_address = await address_crud.update(
        db=db,
        db_obj=address,
        obj_in=address_in
    )
    
    await invalidate_specific_address(current_user.user_id, address_id)
    await invalidate_user_addresses(current_user.user_id)
    
    return updated_address


@router.delete("/me/addresses/{address_id}", response_model=Message)
async def delete_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
) -> Message:
    """
    Xóa một địa chỉ khỏi sổ địa chỉ.
    """
    result = await address_crud.delete_user_address(
        db=db,
        address_id=address_id,
        user_id=current_user.user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy địa chỉ"
        )
    
    await invalidate_specific_address(current_user.user_id, address_id)
    await invalidate_user_addresses(current_user.user_id)
    
    return Message(message="Xóa địa chỉ thành công")


@router.post("/me/addresses/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    address_id: int,
) -> AddressResponse:
    """
    Đặt một địa chỉ làm địa chỉ mặc định.
    """
    address = await address_crud.set_default(
        db=db,
        address_id=address_id,
        user_id=current_user.user_id
    )
    
    await invalidate_user_addresses(current_user.user_id)
    
    return address



@router.get("", response_model=list[UserResponse])
@cache(expire=60)
async def list_users(
    response: Response,
    db: SessionDep,
    pagination: PaginationDep,
    current_user: User = Depends(require_permission("user.view")),
    search: str | None = Query(None, description="Tìm kiếm theo email, tên"),
    is_active: bool | None = Query(None, description="Lọc theo trạng thái hoạt động"),
    is_superuser: bool | None = Query(None, description="Lọc theo trạng thái superuser"),
) -> list[UserResponse]:
    """
    Lấy danh sách người dùng (Có phân trang, tìm kiếm, lọc).
    """
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    if is_superuser is not None:
        filters["is_superuser"] = is_superuser
    
    users = await user_crud.get_multi(
        db=db,
        skip=pagination.get_offset(),
        limit=pagination.get_limit(),
        filters=filters,
        search=search
    )
    
    total_count = await user_crud.get_count(
        db=db,
        filters=filters,
        search=search
    )
    
    total_pages = (total_count + pagination.page_size - 1) // pagination.page_size if total_count > 0 else 0

    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Total-Pages"] = str(total_pages)
    response.headers["X-Page"] = str(pagination.page)
    response.headers["X-Page-Size"] = str(pagination.page_size)
    
    return users


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("user.create")),
    user_in: UserCreate,
) -> UserResponse:
    """
    Tạo người dùng mới (Dành cho Admin/Superuser).
    
    Logic phân quyền:
    - Superuser (ID 1): Có quyền tạo bất kỳ ai (kể cả Superuser khác).
    - Admin (ID 2): Chỉ được tạo người có Role ID lớn hơn 2 (Staff/Customer).
    """
    user = await user_crud.get_by_email(db=db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng"
        )

    target_role = await role_crud.get(db=db, id=user_in.role_id)
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Role ID {user_in.role_id} không tồn tại"
        )

    is_superuser_flag = False
    
    if user_in.role_id == 1:
        if not current_user.is_superuser:
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN, 
                 detail="Chỉ Superuser mới được phép tạo Superuser khác."
             )
        is_superuser_flag = True
    
    elif not current_user.is_superuser:
        my_role_id = current_user.role_id
        target_role_id = user_in.role_id
        
        if my_role_id >= target_role_id:
             raise HTTPException(
                 status_code=status.HTTP_403_FORBIDDEN, 
                 detail="Không đủ thẩm quyền. Bạn chỉ được tạo tài khoản cấp bậc thấp hơn."
             )

    user = await user_crud.create(
        db, 
        obj_in=user_in, 
        is_superuser=is_superuser_flag
    )

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "ADMIN_CREATE_USER",
        "target_email": user.email,
        "details": f"Admin {current_user.email} đã tạo tài khoản cho {user.email} với Role ID {user.role_id}"
    })

    return user


@router.get("/{user_id}", response_model=UserDetailResponse)
@cache(expire=300, key_builder=admin_user_detail_key_builder)
async def get_user(
    db: SessionDep,
    current_user: User = Depends(require_permission("user.view")),
    user_id: int = 0,
) -> UserDetailResponse:
    """
    Xem chi tiết hồ sơ của một người dùng bất kỳ.
    """
    users = await user_crud.get_multi_with_role(
        db=db,
        filters={"user_id": user_id},
        limit=1
    )
    
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại"
        )
    
    return users[0]


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("user.update")),
    user_id: int,
    user_in: UserUpdate,
) -> UserResponse:
    """
    Cập nhật thông tin người dùng (Dành cho Admin).
    Bao gồm kiểm tra bảo mật ngăn chặn leo thang đặc quyền.
    """
    user_db = await user_crud.get(db=db, id=user_id)
    
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại"
        )
    
    if user_id == current_user.user_id:
        if user_in.is_active is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tự khóa tài khoản của mình")
        if user_in.is_superuser is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tự hủy quyền Superuser")
        if user_in.role_id is not None and user_in.role_id != current_user.role_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể tự đổi vai trò của mình")

    if not current_user.is_superuser:
        if current_user.role_id >= user_db.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không đủ quyền hạn để chỉnh sửa người dùng này."
            )
        
        if user_in.role_id is not None and current_user.role_id >= user_in.role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không đủ quyền hạn để cấp vai trò này."
            )
            
        if user_in.is_superuser is not None:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Superuser mới được thay đổi trạng thái Superuser."
            )

    if user_in.email and user_in.email != user_db.email:
        existing = await user_crud.get_by_email(db=db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email này đã được sử dụng"
            )
    
    updated_user = await user_crud.update(
        db=db,
        db_obj=user_db,
        obj_in=user_in
    )
    
    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "ADMIN_UPDATE_USER",
        "target_user_id": user_id,
        "details": f"Admin {current_user.email} đã cập nhật thông tin user ID {user_id}"
    })

    await invalidate_user_profile(user_id)
    await invalidate_admin_user_view(user_id)
    
    return updated_user


@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    db: SessionDep,
    current_user: User = Depends(require_permission("user.delete")),
    user_id: int = 0,
    permanent: bool = Query(False, description="Xóa vĩnh viễn (Nếu False chỉ xóa mềm)"),
) -> Message:
    """
    Xóa người dùng (Mặc định là Xóa mềm - Soft Delete).
    """
    user = await user_crud.get(db=db, id=user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại"
        )
    
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không thể tự xóa tài khoản của mình"
        )
        
    if not current_user.is_superuser:
        if current_user.role_id >= user.role_id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Không đủ quyền hạn để xóa người dùng này."
            )
    
    await user_crud.delete(db=db, id=user_id, soft_delete=not permanent)
    await invalidate_all_user_caches(user_id)

    await mongo_service.push_log({
        "admin_id": current_user.user_id,
        "action": "DELETE_USER",
        "target_user_id": user_id,
        "is_permanent": permanent,
        "details": f"Admin {current_user.email} đã {'xóa vĩnh viễn' if permanent else 'vô hiệu hóa'} user ID {user_id}"
    })
    
    return Message(message="Xóa người dùng thành công")