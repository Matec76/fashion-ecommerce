from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, or_, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.notification import (
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationPreferences,
    NotificationPreferencesUpdate,
    EmailQueue,
    EmailQueueCreate,
    EmailQueueUpdate,
)

from app.models.enums import NotificationTypeEnum, EmailTypeEnum, EmailStatusEnum


class CRUDNotification(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):

    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        statement = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            statement = statement.where(Notification.is_read == False)
        
        statement = statement.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_unread_count(
        self,
        *,
        db: AsyncSession,
        user_id: int
    ) -> int:
        statement = select(func.count(Notification.notification_id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await db.execute(statement)
        return result.scalar_one()

    async def mark_as_read(
        self,
        *,
        db: AsyncSession,
        notification_id: int,
        user_id: int
    ) -> Optional[Notification]:
        statement = select(Notification).where(
            Notification.notification_id == notification_id,
            Notification.user_id == user_id
        )
        result = await db.execute(statement)
        notification = result.scalar_one_or_none()
        
        if not notification:
            return None
        
        notification.is_read = True
        notification.read_at = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def mark_all_as_read(
        self,
        *,
        db: AsyncSession,
        user_id: int
    ) -> int:
        statement = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
            .values(
                is_read=True,
                read_at=datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
            )
        )
        
        result = await db.execute(statement)
        await db.commit()
        
        return result.rowcount

    async def create_for_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        notification_type: NotificationTypeEnum,
        title: str,
        message: str,
        reference_id: Optional[int] = None
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_id=reference_id,
            is_read=False
        )
        
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def create_bulk(
        self,
        *,
        db: AsyncSession,
        user_ids: List[int],
        notification_type: NotificationTypeEnum,
        title: str,
        message: str,
        reference_id: Optional[int] = None,
        batch_size: int = 100
    ) -> int:
        count = 0
        
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i + batch_size]
            
            notifications = [
                Notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    reference_id=reference_id,
                    is_read=False
                )
                for user_id in batch
            ]
            
            db.add_all(notifications)
            count += len(notifications)
        
        await db.commit()
        return count

    async def delete_old_notifications(
        self,
        *,
        db: AsyncSession,
        days: int = 30
    ) -> int:
        cutoff_date = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None) - timedelta(days=days)
        
        statement = (
            delete(Notification)
            .where(
                Notification.is_read == True,
                Notification.read_at < cutoff_date
            )
        )
        
        result = await db.execute(statement)
        await db.commit()
        
        return result.rowcount


class CRUDNotificationPreferences(CRUDBase[NotificationPreferences, NotificationPreferences, NotificationPreferencesUpdate]):
   
    async def get_by_user(self, *, db: AsyncSession, user_id: int) -> Optional[NotificationPreferences]:
        statement = select(NotificationPreferences).where(NotificationPreferences.user_id == user_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create(self, *, db: AsyncSession, user_id: int) -> NotificationPreferences:
        preferences = await self.get_by_user(db=db, user_id=user_id)
        if not preferences:
            preferences = NotificationPreferences(
                user_id=user_id,
                email_notifications=True,
                push_notifications=True,
                order_updates=True,
                promotions=True,
                product_back_in_stock=True,
                review_responses=True,
                system_announcements=True
            )
            db.add(preferences)
            await db.commit()
            await db.refresh(preferences)
        return preferences

    async def update_preferences(self, *, db: AsyncSession, user_id: int, obj_in: NotificationPreferencesUpdate) -> NotificationPreferences:
        preferences = await self.get_or_create(db=db, user_id=user_id)
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)
        preferences.updated_at = datetime.now(timezone(timedelta(hours=7)))
        db.add(preferences)
        await db.commit()
        await db.refresh(preferences)
        return preferences


class CRUDEmailQueue(CRUDBase[EmailQueue, EmailQueueCreate, EmailQueueUpdate]):
    
    async def get_pending(self, *, db: AsyncSession, limit: int = 100) -> List[EmailQueue]:
        now = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
        statement = select(EmailQueue).where(
            EmailQueue.status == EmailStatusEnum.PENDING,
            EmailQueue.retry_count < EmailQueue.max_retries,
            or_(EmailQueue.scheduled_at == None, EmailQueue.scheduled_at <= now)
        ).order_by(EmailQueue.scheduled_at.nullsfirst(), EmailQueue.created_at).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def create_email(
        self,
        *,
        db: AsyncSession,
        recipient_email: str,
        email_notification_type: EmailTypeEnum,
        subject: str,
        html_body: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None
    ) -> EmailQueue:
        email_queue = EmailQueue(
            recipient_email=recipient_email,
            email_notification_type=email_notification_type,
            subject=subject,
            html_body=html_body,
            context=context,
            scheduled_at=scheduled_at,
            status=EmailStatusEnum.PENDING,
            retry_count=0
        )
        db.add(email_queue)
        await db.commit()
        await db.refresh(email_queue)
        return email_queue

    async def mark_sent(self, *, db: AsyncSession, email_id: int) -> EmailQueue:
        email = await self.get(db=db, id=email_id)
        if not email: raise ValueError("Email not found")
        email.status = EmailStatusEnum.SENT
        email.sent_at = datetime.now(timezone(timedelta(hours=7)))
        db.add(email)
        await db.commit()
        await db.refresh(email)
        return email

    async def mark_failed(self, *, db: AsyncSession, email_id: int, error_message: str) -> EmailQueue:
        email = await self.get(db=db, id=email_id)
        if not email: raise ValueError("Email not found")
        email.retry_count += 1
        email.error_message = error_message
        if email.retry_count >= email.max_retries:
            email.status = EmailStatusEnum.FAILED
        db.add(email)
        await db.commit()
        await db.refresh(email)
        return email

    async def get_by_notification_type(
        self,
        *,
        db: AsyncSession,
        email_notification_type: EmailTypeEnum,
        status: Optional[EmailStatusEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[EmailQueue]:
        statement = select(EmailQueue).where(EmailQueue.email_notification_type == email_notification_type)
        if status:
            statement = statement.where(EmailQueue.status == status)
        statement = statement.order_by(EmailQueue.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def delete_old_emails(self, *, db: AsyncSession, days: int = 30) -> int:
        cutoff_date = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None) - timedelta(days=days)
        statement = delete(EmailQueue).where(
            EmailQueue.status.in_([EmailStatusEnum.SENT, EmailStatusEnum.FAILED]),
            or_(EmailQueue.sent_at < cutoff_date, EmailQueue.created_at < cutoff_date)
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount

    async def get_failed_emails(self, *, db: AsyncSession, limit: int = 100) -> List[EmailQueue]:
        statement = select(EmailQueue).where(EmailQueue.status == EmailStatusEnum.FAILED).order_by(EmailQueue.created_at.desc()).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()


notification = CRUDNotification(Notification)
notification_preferences = CRUDNotificationPreferences(NotificationPreferences)
email_queue = CRUDEmailQueue(EmailQueue)