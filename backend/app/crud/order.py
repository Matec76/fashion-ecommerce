from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func, and_, or_, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.core.config import settings
from app.crud.system import system_setting
from app.crud.base import CRUDBase
from app.models.order import (
    Order,
    OrderCreate,
    OrderUpdate,
    OrderItem,
    OrderItemCreate,
    OrderStatusHistory,
    OrderStatusHistoryCreate,
    ShippingMethod,
    ShippingMethodCreate,
    ShippingMethodUpdate,
)
from app.models.enums import OrderStatusEnum, PaymentStatusEnum, PaymentMethodType
from app.crud.product import product_variant, product as product_crud
from app.crud.cart import cart_item as cart_item_crud


VALID_ORDER_STATUS_TRANSITIONS = {
    OrderStatusEnum.PENDING: [
        OrderStatusEnum.CONFIRMED,
        OrderStatusEnum.CANCELLED
    ],
    OrderStatusEnum.CONFIRMED: [
        OrderStatusEnum.PROCESSING,
        OrderStatusEnum.CANCELLED,
        OrderStatusEnum.REFUNDED,        
        OrderStatusEnum.PARTIAL_REFUNDED
    ],
    OrderStatusEnum.PROCESSING: [
        OrderStatusEnum.SHIPPED,
        OrderStatusEnum.CANCELLED,
        OrderStatusEnum.REFUNDED,          
        OrderStatusEnum.PARTIAL_REFUNDED
    ],
    OrderStatusEnum.SHIPPED: [
        OrderStatusEnum.DELIVERED,
        OrderStatusEnum.CANCELLED,
        OrderStatusEnum.REFUNDED,          
        OrderStatusEnum.PARTIAL_REFUNDED
    ],
    OrderStatusEnum.DELIVERED: [
       OrderStatusEnum.RETURN_REQUESTED,
        OrderStatusEnum.COMPLETED,
        OrderStatusEnum.REFUNDED,
        OrderStatusEnum.PARTIAL_REFUNDED
    ],
    OrderStatusEnum.RETURN_REQUESTED: [
        OrderStatusEnum.REFUNDED,
        OrderStatusEnum.PARTIAL_REFUNDED,
        OrderStatusEnum.COMPLETED
    ],
    OrderStatusEnum.COMPLETED: [],
    OrderStatusEnum.CANCELLED: [],
    OrderStatusEnum.REFUNDED: [],
    OrderStatusEnum.PARTIAL_REFUNDED: [
        OrderStatusEnum.REFUNDED
    ]
}


class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    
    async def get_with_details(
        self,
        *,
        db: AsyncSession,
        id: int
    ) -> Optional[Order]:

        from app.models.coupon import OrderCoupon

        statement = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.variant),
                selectinload(Order.user),
                selectinload(Order.cancelled_user),
                selectinload(Order.shipping_method),
                selectinload(Order.status_history),
                selectinload(Order.payment_method),
                selectinload(Order.payment_transactions),
                selectinload(Order.order_coupons).selectinload(OrderCoupon.coupon),
            )
            .where(Order.order_id == id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_order_number(
        self,
        *,
        db: AsyncSession,
        order_number: str
    ) -> Optional[Order]:
        statement = select(Order).where(Order.order_number == order_number)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[OrderStatusEnum] = None
    ) -> List[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
        )
        
        if status:
            statement = statement.where(Order.order_status == status)
        
        statement = statement.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def create_from_cart(
        self,
        *,
        db: AsyncSession,
        cart_id: int,
        user_id: int,
        shipping_address_id: int,
        billing_address_id: int,
        shipping_method_id: int,
        payment_method_id: int,
        notes: Optional[str] = None,
        coupon_code: Optional[str] = None,
        order_ip: Optional[str] = None,
        order_device: Optional[str] = None,
        commit: bool = True
    ) -> Order:
        """
        Atomic operations for stock, coupon, and order number
        """
        from app.crud.user import user as user_crud
        from app.crud.address import address as address_crud
        from app.crud.payment_method import payment_method as pm_crud
        from app.models.coupon import OrderCoupon

        cart_items = await cart_item_crud.get_by_cart(db=db, cart_id=cart_id)
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        user = await user_crud.get(db=db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        shipping_addr = await address_crud.get(db=db, id=shipping_address_id)
        if not shipping_addr:
            raise HTTPException(status_code=404, detail="Shipping address not found")
        
        billing_addr = await address_crud.get(db=db, id=billing_address_id)
        if not billing_addr:
            raise HTTPException(status_code=404, detail="Billing address not found")
        
        shipping_method_obj = await shipping_method.get(db=db, id=shipping_method_id)
        if not shipping_method_obj:
            raise HTTPException(status_code=404, detail="Shipping method not found")
        
        payment_method_obj = await pm_crud.get(db=db, id=payment_method_id)
        if not payment_method_obj or not payment_method_obj.is_active:
            raise HTTPException(status_code=400, detail="Invalid payment method")
        
        supported_methods = [
            PaymentMethodType.BANK_TRANSFER.value,
            PaymentMethodType.COD.value
        ]
        if payment_method_obj.method_code not in supported_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Payment method '{payment_method_obj.method_code}' is not supported"
            )
        
        subtotal = Decimal("0.00")
        validated_items = []
        
        for cart_item in cart_items:
            variant = await product_variant.get_with_details(db=db, id=cart_item.variant_id)
            
            if not variant:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product variant {cart_item.variant_id} not found"
                )
            
            if not variant.is_available:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product {variant.sku} is not available"
                )
            
            current_price = variant.product.sale_price if variant.product.sale_price else variant.product.base_price
            item_subtotal = current_price * cart_item.quantity
            
            validated_items.append({
                "cart_item": cart_item,
                "variant": variant,
                "unit_price": current_price,
                "item_subtotal": item_subtotal
            })
            
            subtotal += item_subtotal
        
        shipping_fee = shipping_method_obj.base_cost
        free_shipping_reason = None

        free_ship_threshold = await system_setting.get_value(
            db=db, 
            key="free_shipping_threshold", 
            default="500000"
        )
        
        if subtotal >= Decimal(free_ship_threshold):
            shipping_fee = Decimal("0.00")
            free_shipping_reason = "order_threshold"

        discount_amount = Decimal("0.00")
        coupon_obj = None
        now = datetime.now(timezone(timedelta(hours=7)))
        
        if coupon_code:
            from app.crud.coupon import coupon as coupon_crud_obj
            
            validation_result = await coupon_crud_obj.validate_coupon(
                db=db,
                code=coupon_code,
                user_id=user_id,
                order_amount=subtotal
            )

            if not validation_result.valid:
                raise HTTPException(
                    status_code=400,
                    detail=validation_result.error or "Mã giảm giá không hợp lệ"
                )
            
            discount_amount = validation_result.discount_amount
            validated_data = validation_result.coupon
            
            coupon_obj = await coupon_crud_obj.get(db=db, id=validated_data.coupon_id)
            
            if coupon_obj:
                coupon_obj.used_count += 1
                db.add(coupon_obj)

                if coupon_obj.free_shipping:
                    shipping_fee = Decimal("0.00")
                    free_shipping_reason = "coupon"
        
        tax_amount = subtotal * Decimal("0.1")
        total_amount = subtotal + shipping_fee - discount_amount + tax_amount
        if total_amount < 0:
            total_amount = Decimal("0.00")
        
        user_snapshot = {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
        }
        
        shipping_metadata = {
            "original_fee": float(shipping_method_obj.base_cost),
            "applied_fee": float(shipping_fee),
            "free_shipping_applied": shipping_fee == Decimal("0.00"),
            "free_shipping_reason": free_shipping_reason
        }
        
        shipping_snapshot = {
            "address_id": shipping_addr.address_id,
            "recipient_name": shipping_addr.recipient_name,
            "phone_number": shipping_addr.phone_number,
            "street_address": shipping_addr.street_address,
            "ward": shipping_addr.ward,
            "city": shipping_addr.city,
            "postal_code": shipping_addr.postal_code,
            "shipping_metadata": shipping_metadata
        }
        
        billing_snapshot = {
            "address_id": billing_addr.address_id,
            "recipient_name": billing_addr.recipient_name,
            "phone_number": billing_addr.phone_number,
            "street_address": billing_addr.street_address,
            "ward": billing_addr.ward,
            "city": billing_addr.city,
            "postal_code": billing_addr.postal_code,
        }
        
        order_number = await self.generate_order_number(db=db)
        
        order = Order(
            user_id=user_id,
            order_number=order_number,
            order_status=OrderStatusEnum.PENDING,
            payment_status=PaymentStatusEnum.PENDING,
            payment_method_id=payment_method_id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            shipping_method_id=shipping_method_id,
            user_snapshot=user_snapshot,
            shipping_snapshot=shipping_snapshot,
            billing_snapshot=billing_snapshot,
            notes=notes,
            order_ip=order_ip,
            order_device=order_device,
            created_at=now
        )
        
        db.add(order)
        await db.flush()
        
        for item_data in validated_items:
            cart_item = item_data["cart_item"]
            variant = item_data["variant"]
            
            order_item = OrderItem(
                order_id=order.order_id,
                variant_id=variant.variant_id,
                product_name=variant.product.product_name,
                sku=variant.sku,
                color=variant.color.color_name if variant.color else None,
                size=variant.size.size_name if variant.size else None,
                quantity=cart_item.quantity,
                unit_price=item_data["unit_price"],
                subtotal=item_data["item_subtotal"]
            )
            db.add(order_item)
    
            success = await product_variant.update_stock_with_lock(
                db=db,
                variant_id=variant.variant_id,
                quantity=cart_item.quantity,
                increment=False
            )
            
            if not success:
                await db.rollback()
                raise HTTPException(
                    status_code=400, 
                    detail=f"Sản phẩm {variant.sku} không đủ số lượng hoặc đã hết hàng trong quá trình thanh toán"
                )
            
            await product_crud.update_sold_count(
                db=db,
                product_id=variant.product_id,
                quantity=cart_item.quantity
            )

        if coupon_obj:
            order_coupon = OrderCoupon(
                order_id=order.order_id,
                coupon_id=coupon_obj.coupon_id,
                discount_amount=discount_amount
            )
            db.add(order_coupon)
        
        status_history = OrderStatusHistory(
            order_id=order.order_id,
            old_status=None,
            new_status=OrderStatusEnum.PENDING,
            comment="Order created",
            created_by=user_id,
            created_at=now
        )
        db.add(status_history)
    
        
        if commit:
            try:
                await db.commit()
                await db.refresh(order)
            except Exception as e:
                await db.rollback()
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        else:
            await db.flush()
        
        return order

    async def generate_order_number(
        self,
        *,
        db: AsyncSession
    ) -> str:
        """
        Atomic order number generation using PostgreSQL Sequence
        Tạo sequence mới mỗi ngày để reset counter
        """
        today = datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d")
        seq_name = f"order_seq_{today}"
        
        await db.execute(text(f"""
            CREATE SEQUENCE IF NOT EXISTS {seq_name}
            START WITH 1
            INCREMENT BY 1
            NO MAXVALUE
            NO CYCLE
        """))
        
        result = await db.execute(text(f"SELECT nextval('{seq_name}')"))
        sequence = result.scalar()
        
        order_number = f"{settings.ORDER_NUMBER_PREFIX}-{today}-{sequence:05d}"
        
        return order_number

    async def update_status(
        self,
        *,
        db: AsyncSession,
        order_id: int,
        new_status: OrderStatusEnum,
        user_id: int,
        note: Optional[str] = None,
        expected_status: Optional[OrderStatusEnum] = None
    ) -> Order:
        """
        Atomic status update với validation
        """

        from app.models.coupon import OrderCoupon

        stmt = (
            update(Order)
            .where(Order.order_id == order_id)
        )
        
        if expected_status:
            stmt = stmt.where(Order.order_status == expected_status)
        else:
            stmt = stmt.where(
                Order.order_status.notin_([
                    OrderStatusEnum.DELIVERED,
                    OrderStatusEnum.CANCELLED
                ])
            )
        
        stmt = stmt.where(Order.order_status != new_status)
        
        stmt = (
            stmt
            .values(
                order_status=new_status,
                updated_at=datetime.now(timezone(timedelta(hours=7)))
            )
            .returning(Order)
        )
        
        result = await db.execute(stmt)
        updated_order = result.scalar_one_or_none()
        
        if not updated_order:
            current_order = await self.get(db=db, id=order_id)
            if not current_order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            if expected_status and current_order.order_status != expected_status:
                raise HTTPException(
                    status_code=409,
                    detail=f"Order status conflict. Expected {expected_status.value}, got {current_order.order_status.value}"
                )
        
            return current_order
        
        history = OrderStatusHistory(
            order_id=order_id,
            old_status=expected_status,
            new_status=new_status,
            comment=note,
            created_by=user_id,
            created_at=datetime.now(timezone(timedelta(hours=7)))
        )
        db.add(history)
        
        if new_status in [OrderStatusEnum.CANCELLED, OrderStatusEnum.REFUNDED]:
            items = await order_item.get_by_order(db=db, order_id=order_id)
            for item in items:
                if item.variant_id:
                    await product_variant.update_stock_with_lock(
                        db=db,
                        variant_id=item.variant_id,
                        quantity=item.quantity,
                        increment=True
                    )

                if item.variant:
                        await product_crud.update_sold_count(
                            db=db,
                            product_id=item.variant.product_id,
                            quantity= -item.quantity
                        )
            
            stmt_coupon = (
                select(OrderCoupon)
                .options(selectinload(OrderCoupon.coupon))
                .where(OrderCoupon.order_id == order_id)
            )
            result_coupon = await db.execute(stmt_coupon)
            order_coupons = result_coupon.scalars().all()
            
            for oc in order_coupons:
                if oc.coupon:
                    oc.coupon.used_count = max(0, oc.coupon.used_count - 1)
                    db.add(oc.coupon)
                    await db.delete(oc)
        
        await db.commit()
        await db.refresh(updated_order)
        return updated_order
    
    async def get_by_status(
        self,
        *,
        db: AsyncSession,
        status: OrderStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        statement = (
            select(Order)
            .where(Order.order_status == status)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_pending_orders(
        self,
        *,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 100
    ) -> List[Order]:
        cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(hours=hours)
        
        statement = (
            select(Order)
            .where(
                Order.order_status == OrderStatusEnum.PENDING,
                Order.created_at < cutoff_time
            )
            .order_by(Order.created_at)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_revenue_by_date_range(
        self,
        *,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        statement = select(func.sum(Order.total_amount)).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.order_status.in_([
                    OrderStatusEnum.CONFIRMED,
                    OrderStatusEnum.PROCESSING,
                    OrderStatusEnum.SHIPPED,
                    OrderStatusEnum.DELIVERED
                ])
            )
        )
        result = await db.execute(statement)
        total = result.scalar_one()
        return total if total else Decimal("0.00")

    async def search(
        self,
        *,
        db: AsyncSession,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        from app.models.user import User
        
        statement = (
            select(Order)
            .join(User)
            .where(
                or_(
                    Order.order_number.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                    User.phone_number.ilike(f"%{query}%")
                )
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())
    
    async def count_by_date_range(
        self,
        *,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Đếm số đơn hàng trong khoảng thời gian."""
        statement = select(func.count(Order.order_id)).where(
            and_(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.order_status != OrderStatusEnum.CANCELLED
            )
        )
        result = await db.execute(statement)
        return result.scalar() or 0

    async def get_sales_stats_by_period(
        self, 
        *, 
        db: AsyncSession, 
        start_date: datetime, 
        end_date: datetime, 
        period: str = "day"
    ) -> List[dict]:
        """Thống kê biểu đồ doanh thu."""
        trunc_interval = {
            "hourly": "hour", "daily": "day", "weekly": "week", "monthly": "month", "yearly": "year"
        }.get(period, "day")

        date_col = func.date_trunc(trunc_interval, Order.created_at).label("period_date")

        statement = (
            select(
                date_col,
                func.count(Order.order_id).label("total_orders"),
                func.sum(Order.total_amount).label("revenue")
            )
            .where(
                Order.created_at >= start_date,
                Order.created_at <= end_date,
                Order.order_status.in_([
                    OrderStatusEnum.COMPLETED, 
                    OrderStatusEnum.DELIVERED,
                    OrderStatusEnum.SHIPPED
                ])
            )
            .group_by(date_col)
            .order_by(date_col)
        )

        result = await db.execute(statement)
        return [
            {
                "date": row.period_date.isoformat(),
                "total_orders": row.total_orders,
                "revenue": float(row.revenue or 0)
            }
            for row in result.all()
        ]


class CRUDOrderItem(CRUDBase[OrderItem, OrderItemCreate, Dict[str, Any]]):
    
    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> List[OrderItem]:
        statement = (
            select(OrderItem)
            .options(selectinload(OrderItem.variant))
            .where(OrderItem.order_id == order_id)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())


class CRUDOrderStatusHistory(CRUDBase[OrderStatusHistory, OrderStatusHistoryCreate, Dict[str, Any]]):
    
    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> List[OrderStatusHistory]:
        statement = (
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.created_at.desc())
        )
        result = await db.execute(statement)
        return list(result.scalars().all())


class CRUDShippingMethod(CRUDBase[ShippingMethod, ShippingMethodCreate, ShippingMethodUpdate]):
    
    async def get_active(
        self,
        *,
        db: AsyncSession
    ) -> List[ShippingMethod]:
        statement = (
            select(ShippingMethod)
            .where(ShippingMethod.is_active == True)
            .order_by(ShippingMethod.base_cost)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_name(
        self,
        *,
        db: AsyncSession,
        name: str
    ) -> Optional[ShippingMethod]:
        statement = select(ShippingMethod).where(ShippingMethod.method_name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()


order = CRUDOrder(Order)
order_item = CRUDOrderItem(OrderItem)
order_status_history = CRUDOrderStatusHistory(OrderStatusHistory)
shipping_method = CRUDShippingMethod(ShippingMethod)