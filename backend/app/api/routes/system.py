from typing import Any, List, Dict

from fastapi import APIRouter, Query, status, HTTPException, BackgroundTasks
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    SuperUser
)
from app.crud.system import system_setting as setting_crud
from app.services.mongo_service import mongo_service

from app.models.system import (
    SystemSettingResponse,
    SystemSettingCreate,
    SystemSettingUpdate,
    AdminActivityLogResponse,
)
from app.models.enums import AdminActionEnum, SettingTypeEnum
from app.models.common import Message

router = APIRouter()

async def bg_log_activity(
    user_id: int, 
    user_email: str,
    action: AdminActionEnum, 
    table: str, 
    record_id: Any, 
    old: Dict = None, 
    new: Dict = None
):
    """
    Tác vụ chạy nền: Đóng gói và đẩy dữ liệu nhật ký hoạt động của Admin vào MongoDB.
    """
    log_data = {
        "user_id": user_id,
        "user_email": user_email,
        "action_type": action,
        "table_name": table,
        "record_id": str(record_id),
        "old_value": old,
        "new_value": new
    }
    await mongo_service.push_log(log_data)


@router.get("/settings/public", response_model=dict[str, Any])
@cache(expire=3600, namespace="system-settings")
async def get_public_settings(
    db: SessionDep,
) -> dict[str, Any]:
    """
    Lấy toàn bộ danh sách các cấu hình hệ thống được phép công khai cho phía Client.
    """
    return await setting_crud.get_all_as_dict(db=db, public_only=True)


@router.get("/settings/public/{key}", response_model=Any)
@cache(expire=3600, namespace="system-settings")
async def get_public_setting_by_key(
    db: SessionDep,
    key: str,
) -> Any:
    """
    Lấy giá trị của một cấu hình công khai cụ thể dựa trên từ khóa (Key).
    """
    setting = await setting_crud.get_by_key(db=db, key=key)
    
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    if not setting.is_public:
        raise HTTPException(status_code=403, detail="This setting is not public")
    
    value = await setting_crud.get_value(db=db, key=key)
    return {"key": key, "value": value}


@router.get("/settings", response_model=List[SystemSettingResponse])
async def list_settings(
    db: SessionDep,
    current_user: SuperUser,
) -> List[SystemSettingResponse]:
    """
    Liệt kê tất cả các cấu hình hệ thống (Chỉ dành cho SuperUser).
    """
    return await setting_crud.get_multi(db=db, limit=1000)


@router.get("/settings/{setting_id}", response_model=SystemSettingResponse)
async def get_setting(
    db: SessionDep,
    setting_id: int,
    current_user: SuperUser,
) -> SystemSettingResponse:
    """
    Xem thông tin chi tiết của một cấu hình dựa trên ID (Chỉ dành cho SuperUser).
    """
    setting = await setting_crud.get(db=db, id=setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


@router.get("/settings/key/{key}", response_model=SystemSettingResponse)
async def get_setting_by_key(
    db: SessionDep,
    key: str,
    current_user: SuperUser,
) -> SystemSettingResponse:
    """
    Truy vấn cấu hình hệ thống dựa trên từ khóa Key (Chỉ dành cho SuperUser).
    """
    setting = await setting_crud.get_by_key(db=db, key=key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting


@router.post("/settings", response_model=SystemSettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting(
    *,
    db: SessionDep,
    current_user: SuperUser,
    setting_in: SystemSettingCreate,
    background_tasks: BackgroundTasks,
) -> SystemSettingResponse:
    """
    Tạo mới một cấu hình hệ thống và ghi lại nhật ký hoạt động (Chỉ dành cho SuperUser).
    """
    existing = await setting_crud.get_by_key(db=db, key=setting_in.setting_key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setting key already exists"
        )
    
    setting_in.updated_by = current_user.user_id
    
    setting = await setting_crud.create(db=db, obj_in=setting_in)
    
    await FastAPICache.clear(namespace="system-settings")
    
    background_tasks.add_task(
        bg_log_activity,
        user_id=current_user.user_id,
        user_email=current_user.email,
        action=AdminActionEnum.CREATE,
        table="system_settings",
        record_id=setting.setting_id,
        new=setting_in.model_dump()
    )
    
    return setting


@router.patch("/settings/{setting_id}", response_model=SystemSettingResponse)
async def update_setting(
    *,
    db: SessionDep,
    current_user: SuperUser,
    setting_id: int,
    setting_in: SystemSettingUpdate,
    background_tasks: BackgroundTasks,
) -> SystemSettingResponse:
    """
    Cập nhật giá trị cấu hình và ghi lại nhật ký thay đổi (Chỉ dành cho SuperUser).
    """
    setting = await setting_crud.get(db=db, id=setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    old_value = {
        "setting_value": setting.setting_value,
        "setting_type": setting.setting_type.value if setting.setting_type else None,
        "is_public": setting.is_public
    }
    
    setting_in.updated_by = current_user.user_id
    
    updated_setting = await setting_crud.update(
        db=db,
        db_obj=setting,
        obj_in=setting_in
    )
    
    new_value = {
        "setting_value": updated_setting.setting_value,
        "setting_type": updated_setting.setting_type.value if updated_setting.setting_type else None,
        "is_public": updated_setting.is_public
    }
    
    await FastAPICache.clear(namespace="system-settings")
    
    background_tasks.add_task(
        bg_log_activity,
        user_id=current_user.user_id,
        user_email=current_user.email,
        action=AdminActionEnum.UPDATE,
        table="system_settings",
        record_id=setting_id,
        old=old_value,
        new=new_value
    )
    
    return updated_setting


@router.delete("/settings/{setting_id}", response_model=Message)
async def delete_setting(
    db: SessionDep,
    setting_id: int,
    background_tasks: BackgroundTasks,
    current_user: SuperUser,
) -> Message:
    """
    Xóa vĩnh viễn một cấu hình khỏi hệ thống (Chỉ dành cho SuperUser).
    """
    setting = await setting_crud.get(db=db, id=setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    old_value = {
        "key": setting.setting_key,
        "value": setting.setting_value
    }
    
    await setting_crud.delete(db=db, id=setting_id)
    
    await FastAPICache.clear(namespace="system-settings")
    
    background_tasks.add_task(
        bg_log_activity,
        user_id=current_user.user_id,
        user_email=current_user.email,
        action=AdminActionEnum.DELETE,
        table="system_settings",
        record_id=setting_id,
        old=old_value
    )
    
    return Message(message="Setting deleted successfully")


@router.post("/settings/set", response_model=SystemSettingResponse)
async def set_setting_value(
    *,
    db: SessionDep,
    current_user: SuperUser,
    key: str,
    value: Any,
    background_tasks: BackgroundTasks,
    type: str = "string",
    description: str | None = None,
    is_public: bool = False,
) -> SystemSettingResponse:
    """
    Thiết lập hoặc cập nhật nhanh (Upsert) giá trị cho một Key cấu hình hệ thống.
    """
    
    try:
        setting_type_enum = SettingTypeEnum(type)
    except ValueError:
        setting_type_enum = SettingTypeEnum.STRING

    setting = await setting_crud.set_value(
        db=db,
        key=key,
        value=value,
        type=setting_type_enum,
        description=description,
        is_public=is_public,
        updated_by=current_user.user_id
    )
    
    await FastAPICache.clear(namespace="system-settings")
    
    background_tasks.add_task(
        bg_log_activity,
        user_id=current_user.user_id,
        user_email=current_user.email,
        action=AdminActionEnum.UPDATE,
        table="system_settings",
        record_id=setting.setting_id,
        new={"key": key, "value": str(value)}
    )
    
    return setting


@router.get("/logs", response_model=List[AdminActivityLogResponse])
async def list_activity_logs(
    current_user: SuperUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    hours: int = Query(24, description="Hours to look back (optional)"),
) -> List[AdminActivityLogResponse]:
    """
    Liệt kê danh sách các nhật ký hoạt động gần đây của Admin từ MongoDB.
    """
    return await mongo_service.get_logs(skip=skip, limit=limit)


@router.get("/logs/user/{user_id}", response_model=List[AdminActivityLogResponse])
async def get_user_activity_logs(
    user_id: int,
    current_user: SuperUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[AdminActivityLogResponse]:
    """
    Truy vấn lịch sử hoạt động của một Admin cụ thể dựa trên User ID.
    """
    return await mongo_service.get_logs(
        filter_query={"user_id": user_id},
        skip=skip,
        limit=limit
    )


@router.get("/logs/table/{table_name}", response_model=List[AdminActivityLogResponse])
async def get_table_activity_logs(
    table_name: str,
    current_user: SuperUser,
    record_id: str | None = Query(None, description="Specific record ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[AdminActivityLogResponse]:
    """
    Lấy danh sách nhật ký tác động lên một bảng dữ liệu hoặc một bản ghi (Record) cụ thể.
    """
    query = {"table_name": table_name}
    if record_id:
        query["record_id"] = str(record_id)
        
    return await mongo_service.get_logs(
        filter_query=query,
        skip=skip,
        limit=limit
    )


@router.delete("/logs/cleanup", response_model=Message)
async def cleanup_old_logs(
    current_user: SuperUser,
    days: int = Query(90, description="Delete logs older than X days"),
) -> Message:
    """
    Xóa bỏ các bản ghi nhật ký hoạt động đã cũ để giải phóng dung lượng lưu trữ (Mặc định > 90 ngày).
    """
    count = await mongo_service.delete_old_logs(days=days)
    return Message(message=f"Deleted {count} old activity logs")