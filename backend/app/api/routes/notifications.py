from fastapi import APIRouter, Query, status, HTTPException, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    CurrentUser,
    require_permission,
)
from app.crud.notification import notification as notification_crud
from app.crud.notification import notification_preferences as preferences_crud
from app.models.notification import (
    NotificationResponse,
    NotificationCreate,
    NotificationBulkCreate,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
)
from app.models.common import Message
from app.models.enums import NotificationTypeEnum
from app.models.user import User

router = APIRouter()


def unread_count_key_builder(func, namespace: str = "", *args, **kwargs):
    user_obj = kwargs.get("current_user")
    user_id = user_obj.user_id if hasattr(user_obj, "user_id") else "guest"
    return f"{namespace}:user:{user_id}:count"

def preferences_key_builder(func, namespace: str = "", *args, **kwargs):
    user_obj = kwargs.get("current_user")
    user_id = user_obj.user_id if hasattr(user_obj, "user_id") else "guest"
    return f"{namespace}:user:{user_id}"


@router.get("/me", response_model=list[NotificationResponse])
async def get_my_notifications(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="Only unread notifications"),
) -> list[NotificationResponse]:
    """
    Lấy danh sách các thông báo của người dùng hiện tại (Có phân trang và lọc theo trạng thái chưa đọc).
    """
    notifications = await notification_crud.get_by_user(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    return [
        NotificationResponse(
            notification_id=n.notification_id,
            user_id=n.user_id,
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            reference_id=n.reference_id,
            is_read=n.is_read,
            created_at=n.created_at,
            read_at=n.read_at
        )
        for n in notifications
    ]


@router.get("/me/unread-count", response_model=dict)
@cache(expire=60, namespace="notifications:unread_count", key_builder=unread_count_key_builder)
async def get_unread_count(
    db: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Đếm tổng số lượng thông báo chưa đọc của người dùng hiện tại.
    """
    count = await notification_crud.get_unread_count(
        db=db,
        user_id=current_user.user_id
    )
    
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    notification_id: int,
) -> NotificationResponse:
    """
    Đánh dấu một thông báo cụ thể là đã đọc.
    """
    notification = await notification_crud.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.user_id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    
    return NotificationResponse(
        notification_id=notification.notification_id,
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        reference_id=notification.reference_id,
        is_read=notification.is_read,
        created_at=notification.created_at,
        read_at=notification.read_at
    )


@router.post("/mark-all-read", response_model=Message)
async def mark_all_read(
    db: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """
    Đánh dấu toàn bộ thông báo của người dùng là đã đọc.
    """
    count = await notification_crud.mark_all_as_read(
        db=db,
        user_id=current_user.user_id
    )
    
    return Message(message=f"{count} notifications marked as read")


@router.delete("/cleanup", response_model=Message)
async def cleanup_old_notifications(
    db: SessionDep,
    current_user: User = Depends(require_permission("notification.manage")),
    days: int = Query(30, ge=7, le=365, description="Delete notifications older than N days"),
) -> Message:
    """
    Dọn dẹp hệ thống bằng cách xóa bỏ các thông báo đã cũ vượt quá số ngày quy định.
    """
    count = await notification_crud.delete_old_notifications(
        db=db,
        days=days
    )
    
    return Message(message=f"{count} old notifications deleted")


@router.delete("/{notification_id}", response_model=Message)
async def delete_notification(
    db: SessionDep,
    current_user: CurrentUser,
    notification_id: int,
) -> Message:
    """
    Xóa vĩnh viễn một thông báo khỏi danh sách của người dùng.
    """
    notification = await notification_crud.get(db=db, id=notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    if notification.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this notification"
        )
    
    await notification_crud.delete(db=db, id=notification_id)
    
    return Message(message="Notification deleted successfully")


@router.get("/preferences", response_model=NotificationPreferencesResponse)
@cache(expire=300, namespace="preferences", key_builder=preferences_key_builder)
async def get_notification_preferences(
    db: SessionDep,
    current_user: CurrentUser,
) -> NotificationPreferencesResponse:
    """
    Lấy thông tin cấu hình tùy chọn nhận thông báo của người dùng (Email, Push, v.v.).
    """
    preferences = await preferences_crud.get_or_create(
        db=db,
        user_id=current_user.user_id
    )
    
    return NotificationPreferencesResponse(
        preference_id=preferences.preference_id,
        user_id=preferences.user_id,
        email_notifications=preferences.email_notifications,
        push_notifications=preferences.push_notifications,
        order_updates=preferences.order_updates,
        promotions=preferences.promotions,
        product_back_in_stock=preferences.product_back_in_stock,
        review_responses=preferences.review_responses,
        system_announcements=preferences.system_announcements,
        updated_at=preferences.updated_at
    )


@router.patch("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    preferences_in: NotificationPreferencesUpdate,
) -> NotificationPreferencesResponse:
    """
    Cập nhật các tùy chọn nhận thông báo theo nhu cầu của người dùng.
    """
    preferences = await preferences_crud.update_preferences(
        db=db,
        user_id=current_user.user_id,
        obj_in=preferences_in
    )
    
    await FastAPICache.clear(namespace="preferences")
    
    return NotificationPreferencesResponse(
        preference_id=preferences.preference_id,
        user_id=preferences.user_id,
        email_notifications=preferences.email_notifications,
        push_notifications=preferences.push_notifications,
        order_updates=preferences.order_updates,
        promotions=preferences.promotions,
        product_back_in_stock=preferences.product_back_in_stock,
        review_responses=preferences.review_responses,
        system_announcements=preferences.system_announcements,
        updated_at=preferences.updated_at
    )


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("notification.manage")),
    notification_in: NotificationCreate,
) -> NotificationResponse:
    """
    Tạo và gửi một thông báo mới cho một người dùng cụ thể (Dành cho Admin).
    """
    notification = await notification_crud.create_for_user(
        db=db,
        user_id=notification_in.user_id,
        notification_type=notification_in.notification_type,
        title=notification_in.title,
        message=notification_in.message,
        reference_id=notification_in.reference_id
    )
    
    return NotificationResponse(
        notification_id=notification.notification_id,
        user_id=notification.user_id,
        notification_type=notification.notification_type,
        title=notification.title,
        message=notification.message,
        reference_id=notification.reference_id,
        is_read=notification.is_read,
        created_at=notification.created_at,
        read_at=notification.read_at
    )


@router.post("/bulk", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_bulk_notifications(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("notification.manage")),
    bulk_in: NotificationBulkCreate,
) -> Message:
    """
    Gửi thông báo đồng loạt cho một danh sách ID người dùng (Tối đa 1000 người/lần).
    """
    if len(bulk_in.user_ids) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send to more than 1000 users at once. Use broadcast endpoint for larger groups."
        )
    
    count = await notification_crud.create_bulk(
        db=db,
        user_ids=bulk_in.user_ids,
        notification_type=bulk_in.notification_type,
        title=bulk_in.title,
        message=bulk_in.message,
        reference_id=bulk_in.reference_id
    )
    
    return Message(message=f"{count} notifications created successfully")


@router.post("/broadcast", response_model=Message, status_code=status.HTTP_201_CREATED)
async def broadcast_notification(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("notification.manage")),
    notification_type: NotificationTypeEnum = Query(..., description="Notification Type"),
    title: str = Query(..., min_length=1, max_length=255),
    message: str = Query(..., min_length=1),
    reference_id: int | None = Query(None),
    limit: int = Query(10000, ge=100, le=50000, description="Max users to notify"),
) -> Message:
    """
    Gửi thông báo quảng bá (Broadcast) cho toàn bộ người dùng đang hoạt động trên hệ thống.
    """
    from app.crud.user import user as user_crud
    
    skip = 0
    batch_size = 500
    total_count = 0
    
    while skip < limit:
        users = await user_crud.get_multi(
            db=db,
            skip=skip,
            limit=min(batch_size, limit - skip)
        )
        
        if not users:
            break
        
        user_ids = [user.user_id for user in users if user.is_active]
        
        if user_ids:
            count = await notification_crud.create_bulk(
                db=db,
                user_ids=user_ids,
                notification_type=notification_type,
                title=title,
                message=message,
                reference_id=reference_id,
                batch_size=100
            )
            total_count += count
        
        skip += batch_size
    
    return Message(message=f"Broadcast sent to {total_count} users")


@router.get("/emails/pending", response_model=list)
async def get_pending_emails(
    db: SessionDep,
    current_user: User = Depends(require_permission("notification.manage")),
    limit: int = Query(50, ge=1, le=100),
) -> list:
    """
    Truy vấn danh sách các email đang nằm trong hàng đợi chờ được hệ thống gửi đi.
    """
    from app.crud.notification import email_queue as email_crud
    
    emails = await email_crud.get_pending(db=db, limit=limit)
    
    return [
        {
            "email_id": e.email_id,
            "recipient_email": e.recipient_email,
            "email_notification_type": e.email_notification_type,
            "subject": e.subject,
            "status": e.status,
            "retry_count": e.retry_count,
            "scheduled_at": e.scheduled_at,
            "created_at": e.created_at
        }
        for e in emails
    ]


@router.get("/emails/failed", response_model=list)
async def get_failed_emails(
    db: SessionDep,
    current_user: User = Depends(require_permission("notification.manage")),
    limit: int = Query(50, ge=1, le=100),
) -> list:
    """
    Xem danh sách các email không thể gửi đi sau khi đã thử lại theo cấu hình.
    """
    from app.crud.notification import email_queue as email_crud
    
    emails = await email_crud.get_failed_emails(db=db, limit=limit)
    
    return [
        {
            "email_id": e.email_id,
            "recipient_email": e.recipient_email,
            "email_notification_type": e.email_notification_type,
            "subject": e.subject,
            "status": e.status,
            "retry_count": e.retry_count,
            "error_message": e.error_message,
            "created_at": e.created_at
        }
        for e in emails
    ]


@router.delete("/emails/cleanup", response_model=Message)
async def cleanup_old_emails(
    db: SessionDep,
    current_user: User = Depends(require_permission("notification.manage")),
    days: int = Query(30, ge=7, le=365, description="Delete emails older than N days"),
) -> Message:
    """
    Xóa bỏ lịch sử và hàng đợi email đã được xử lý lâu hơn số ngày quy định.
    """
    from app.crud.notification import email_queue as email_crud
    
    count = await email_crud.delete_old_emails(
        db=db,
        days=days
    )
    
    return Message(message=f"{count} old emails deleted")