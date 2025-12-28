import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.core.db import async_session_maker
from app.models.order import Order, OrderStatusHistory
from app.models.enums import OrderStatusEnum

from app.crud.loyalty import loyalty_point_crud
from app.crud.system import system_setting

logger = logging.getLogger(__name__)

async def auto_complete_orders():
    """
    Tự động chốt đơn DELIVERED quá hạn (theo cấu hình DB) sang COMPLETED.
    Và tự động cộng điểm thưởng (Loyalty Points) cho khách.
    """
    logger.info("START: Chạy tác vụ tự động chốt đơn hàng...")
    
    async with async_session_maker() as db:
        try:
            days_str = await system_setting.get_value(db=db, key="return_window_days", default="7")
            try:
                window_days = int(days_str)
            except ValueError:
                window_days = 7

            cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(days=window_days)
            
            statement = (
                select(Order)
                .where(
                    Order.order_status == OrderStatusEnum.DELIVERED,
                    Order.delivered_at < cutoff_time
                )
            )
            
            results = await db.execute(statement)
            orders = results.scalars().all()
            
            count = 0
            
            for order in orders:
                order.order_status = OrderStatusEnum.COMPLETED
                
                history = OrderStatusHistory(
                    order_id=order.order_id,
                    old_status=OrderStatusEnum.DELIVERED,
                    new_status=OrderStatusEnum.COMPLETED,
                    comment=f"Hệ thống tự động hoàn tất (Quá hạn đổi trả {window_days} ngày)",
                    created_by=1,
                    created_at=datetime.now(timezone(timedelta(hours=7)))
                )
                db.add(history)
                db.add(order)
                
                try:
                    await loyalty_point_crud.process_order_earning(
                        db=db,
                        order_id=order.order_id,
                        user_id=order.user_id,
                        total_amount=order.total_amount
                    )
                    logger.info(f"Đã cộng điểm cho đơn hàng #{order.order_number}")
                    
                except Exception as e_loyalty:
                    logger.error(f"Lỗi cộng điểm cho đơn {order.order_id}: {e_loyalty}")

                count += 1
            
            await db.commit()
            logger.info(f"FINISH: Đã tự động chốt và cộng điểm cho {count} đơn hàng (Cấu hình {window_days} ngày).")
            
        except Exception as e:
            logger.error(f"ERROR Auto-complete: {e}")
            await db.rollback()