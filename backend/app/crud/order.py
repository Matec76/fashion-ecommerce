"""
CRUD operations cho Order, OrderItem, OrderStatusHistory và ShippingMethod models.

Bao gồm:
- CRUDOrder: CRUD cho Order với create from cart, update status, analytics
- CRUDOrderItem: CRUD cho OrderItem
- CRUDOrderStatusHistory: CRUD cho OrderStatusHistory tracking
- CRUDShippingMethod: CRUD cho ShippingMethod
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.models.enums import OrderStatusEnum
from app.crud.product import product_variant
from app.crud.cart import cart as cart_crud, cart_item as cart_item_crud


class CRUDOrder(CRUDBase[Order, OrderCreate, OrderUpdate]):
    """CRUD operations cho Order"""

    async def get_with_details(
        self,
        *,
        db: AsyncSession,
        id: int
    ) -> Optional[Order]:
        """
        Lấy order kèm items, user, shipping method, status history.
        
        Args:
            db: Database session
            id: Order ID
            
        Returns:
            Order instance với eager loaded relationships
        """
        statement = (
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.variant),
                selectinload(Order.user),
                selectinload(Order.shipping_method),
                selectinload(Order.status_history)
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
        """
        Lấy order theo order number.
        
        Args:
            db: Database session
            order_number: Order number
            
        Returns:
            Order instance hoặc None
        """
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
        """
        Lấy danh sách orders của user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Offset
            limit: Limit
            status: Filter theo status
            
        Returns:
            List Order instances
        """
        statement = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
        )
        
        if status:
            statement = statement.where(Order.order_status == status)
        
        statement = statement.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def create_from_cart(
        self,
        *,
        db: AsyncSession,
        cart_id: int,
        user_id: int,
        shipping_address_id: int,
        billing_address_id: int,
        shipping_method_id: int,
        payment_method: str,
        notes: Optional[str] = None,
        coupon_code: Optional[str] = None
    ) -> Order:
        """
        Tạo order từ cart.
        
        Args:
            db: Database session
            cart_id: Cart ID
            user_id: User ID
            shipping_address_id: Shipping address ID
            billing_address_id: Billing address ID
            shipping_method_id: Shipping method ID
            payment_method: Payment method
            notes: Order notes
            coupon_code: Coupon code (optional)
            
        Returns:
            Order instance đã tạo
        """
        # Lấy cart items
        cart = await cart_crud.get(db=db, id=cart_id)
        cart_items = await cart_item_crud.get_by_cart(db=db, cart_id=cart_id)
        
        if not cart_items:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Lấy shipping method để tính phí
        shipping_method = await shipping_method.get(db=db, id=shipping_method_id)
        
        # Tính tổng giá trị
        subtotal = sum(float(item.subtotal) for item in cart_items)
        shipping_fee = float(shipping_method.fee)
        
        # Áp dụng coupon nếu có
        discount_amount = Decimal("0.00")
        if coupon_code:
            from app.crud.coupon import coupon as coupon_crud
            coupon_obj = await coupon_crud.get_by_code(db=db, code=coupon_code)
            if coupon_obj and coupon_obj.is_active:
                # Tính discount (logic đơn giản, có thể mở rộng)
                if coupon_obj.discount_type == "percentage":
                    discount_amount = Decimal(str(subtotal)) * coupon_obj.discount_value / 100
                else:
                    discount_amount = coupon_obj.discount_value
                
                # Giới hạn max discount
                if coupon_obj.max_discount_amount:
                    discount_amount = min(discount_amount, coupon_obj.max_discount_amount)
        
        total_amount = Decimal(str(subtotal)) + Decimal(str(shipping_fee)) - discount_amount
        
        # Tạo order number (format: ORD-YYYYMMDD-XXXXX)
        order_number = await self.generate_order_number(db=db)
        
        # Tạo order
        order = Order(
            user_id=user_id,
            order_number=order_number,
            order_status=OrderStatusEnum.PENDING,
            subtotal=Decimal(str(subtotal)),
            shipping_fee=Decimal(str(shipping_fee)),
            discount_amount=discount_amount,
            total_amount=total_amount,
            shipping_address_id=shipping_address_id,
            billing_address_id=billing_address_id,
            shipping_method_id=shipping_method_id,
            payment_method=payment_method,
            notes=notes
        )
        
        db.add(order)
        await db.flush()  # Flush để lấy order_id
        
        # Tạo order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.order_id,
                variant_id=cart_item.variant_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                subtotal=cart_item.subtotal
            )
            db.add(order_item)
            
            # Giảm stock
            await product_variant.update_stock(
                db=db,
                variant_id=cart_item.variant_id,
                quantity_change=-cart_item.quantity,
                flush=True
            )
        
        # Tạo status history
        status_history = OrderStatusHistory(
            order_id=order.order_id,
            status=OrderStatusEnum.PENDING,
            note="Order created"
        )
        db.add(status_history)
        
        # Clear cart
        await cart_crud.clear_cart(db=db, cart_id=cart_id)
        
        await db.commit()
        await db.refresh(order)
        return order

    async def generate_order_number(
        self,
        *,
        db: AsyncSession
    ) -> str:
        """
        Tạo order number unique.
        
        Args:
            db: Database session
            
        Returns:
            Order number string (ORD-YYYYMMDD-XXXXX)
        """
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"ORD-{today}-"
        
        # Đếm số orders hôm nay
        statement = select(func.count(Order.order_id)).where(
            Order.order_number.like(f"{prefix}%")
        )
        result = await db.execute(statement)
        count = result.scalar_one()
        
        # Tạo số thứ tự (5 chữ số)
        sequence = str(count + 1).zfill(5)
        
        return f"{prefix}{sequence}"

    async def update_status(
        self,
        *,
        db: AsyncSession,
        order_id: int,
        new_status: OrderStatusEnum,
        note: Optional[str] = None,
        updated_by: Optional[int] = None
    ) -> Order:
        """
        Cập nhật trạng thái order và ghi lịch sử.
        
        Args:
            db: Database session
            order_id: Order ID
            new_status: Trạng thái mới
            note: Ghi chú
            updated_by: User ID thực hiện cập nhật
            
        Returns:
            Order instance đã cập nhật
        """
        order = await self.get(db=db, id=order_id)
        old_status = order.order_status
        
        # Cập nhật status
        order.order_status = new_status
        
        # Cập nhật timestamps đặc biệt
        if new_status == OrderStatusEnum.CONFIRMED:
            order.confirmed_at = datetime.utcnow()
        elif new_status == OrderStatusEnum.SHIPPED:
            order.shipped_at = datetime.utcnow()
        elif new_status == OrderStatusEnum.DELIVERED:
            order.delivered_at = datetime.utcnow()
        elif new_status == OrderStatusEnum.CANCELLED:
            order.cancelled_at = datetime.utcnow()
            # Hoàn lại stock
            items = await order_item.get_by_order(db=db, order_id=order_id)
            for item in items:
                await product_variant.update_stock(
                    db=db,
                    variant_id=item.variant_id,
                    quantity_change=item.quantity,
                    flush=True
                )
        
        db.add(order)
        
        # Ghi lịch sử
        status_history = OrderStatusHistory(
            order_id=order_id,
            status=new_status,
            note=note or f"Status changed from {old_status.value} to {new_status.value}",
            changed_by=updated_by
        )
        db.add(status_history)
        
        await db.commit()
        await db.refresh(order)
        return order

    async def get_by_status(
        self,
        *,
        db: AsyncSession,
        status: OrderStatusEnum,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """
        Lấy orders theo status.
        
        Args:
            db: Database session
            status: Order status
            skip: Offset
            limit: Limit
            
        Returns:
            List Order instances
        """
        statement = (
            select(Order)
            .where(Order.order_status == status)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_pending_orders(
        self,
        *,
        db: AsyncSession,
        hours: int = 24,
        limit: int = 100
    ) -> List[Order]:
        """
        Lấy orders đang pending quá lâu (cần xử lý).
        
        Args:
            db: Database session
            hours: Số giờ pending
            limit: Limit
            
        Returns:
            List Order instances
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
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
        return result.scalars().all()

    async def get_revenue_by_date_range(
        self,
        *,
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> Decimal:
        """
        Tính tổng doanh thu trong khoảng thời gian.
        
        Args:
            db: Database session
            start_date: Ngày bắt đầu
            end_date: Ngày kết thúc
            
        Returns:
            Tổng doanh thu (Decimal)
        """
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
        """
        Tìm kiếm orders theo order_number, user email, phone.
        
        Args:
            db: Database session
            query: Search query
            skip: Offset
            limit: Limit
            
        Returns:
            List Order instances
        """
        from app.models.user import User
        
        statement = (
            select(Order)
            .join(User)
            .where(
                or_(
                    Order.order_number.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%"),
                    User.phone.ilike(f"%{query}%")
                )
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDOrderItem(CRUDBase[OrderItem, OrderItemCreate, Dict[str, Any]]):
    """CRUD operations cho OrderItem"""

    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> List[OrderItem]:
        """
        Lấy tất cả items của order.
        
        Args:
            db: Database session
            order_id: Order ID
            
        Returns:
            List OrderItem instances
        """
        statement = (
            select(OrderItem)
            .options(
                selectinload(OrderItem.variant).selectinload(product_variant.model.product),
                selectinload(OrderItem.variant).selectinload(product_variant.model.color),
                selectinload(OrderItem.variant).selectinload(product_variant.model.size)
            )
            .where(OrderItem.order_id == order_id)
        )
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDOrderStatusHistory(CRUDBase[OrderStatusHistory, OrderStatusHistoryCreate, Dict[str, Any]]):
    """CRUD operations cho OrderStatusHistory"""

    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> List[OrderStatusHistory]:
        """
        Lấy lịch sử thay đổi trạng thái của order.
        
        Args:
            db: Database session
            order_id: Order ID
            
        Returns:
            List OrderStatusHistory instances
        """
        statement = (
            select(OrderStatusHistory)
            .where(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.changed_at.desc())
        )
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDShippingMethod(CRUDBase[ShippingMethod, ShippingMethodCreate, ShippingMethodUpdate]):
    """CRUD operations cho ShippingMethod"""

    async def get_active(
        self,
        *,
        db: AsyncSession
    ) -> List[ShippingMethod]:
        """
        Lấy tất cả shipping methods đang active.
        
        Args:
            db: Database session
            
        Returns:
            List ShippingMethod instances
        """
        statement = (
            select(ShippingMethod)
            .where(ShippingMethod.is_active == True)
            .order_by(ShippingMethod.fee)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_name(
        self,
        *,
        db: AsyncSession,
        name: str
    ) -> Optional[ShippingMethod]:
        """
        Lấy shipping method theo tên.
        
        Args:
            db: Database session
            name: Method name
            
        Returns:
            ShippingMethod instance hoặc None
        """
        statement = select(ShippingMethod).where(ShippingMethod.method_name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()


# Singleton instances
order = CRUDOrder(Order)
order_item = CRUDOrderItem(OrderItem)
order_status_history = CRUDOrderStatusHistory(OrderStatusHistory)
shipping_method = CRUDShippingMethod(ShippingMethod)
