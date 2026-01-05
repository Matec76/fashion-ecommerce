from typing import List, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.crud.base import CRUDBase
from app.models.cart import (
    Cart,
    CartCreate,
    CartUpdate,
    CartItem,
    CartItemCreate,
    CartItemUpdate,
    AbandonedCart,
    AbandonedCartCreate,
    AbandonedCartUpdate,
)
from app.models.product import ProductVariant
from app.crud.system import system_setting


class CRUDCart(CRUDBase[Cart, CartCreate, CartUpdate]):

    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int
    ) -> Optional[Cart]:
        
        statement = (
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).options(
                    selectinload(ProductVariant.product),
                    selectinload(ProductVariant.color),
                    selectinload(ProductVariant.size)
                )
            )
            .where(Cart.user_id == user_id)
            .order_by(Cart.updated_at.desc())
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_session(
        self,
        *,
        db: AsyncSession,
        session_id: str
    ) -> Optional[Cart]:

        statement = (
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).options(
                    selectinload(ProductVariant.product),
                    selectinload(ProductVariant.color),
                    selectinload(ProductVariant.size)
                )
            )
            .where(Cart.session_id == session_id)
            .order_by(Cart.updated_at.desc())
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        db: AsyncSession,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> Cart:
        if user_id:
            cart = await self.get_by_user(db=db, user_id=user_id)
        elif session_id:
            cart = await self.get_by_session(db=db, session_id=session_id)
        else:
            return None
        
        if not cart:
            cart = Cart(
                user_id=user_id,
                session_id=session_id
            )
            db.add(cart)
            await db.commit()
            await db.refresh(cart)
        
        return cart

    async def merge_carts(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        session_id: str
    ) -> Cart:
        user_cart = await self.get_by_user(db=db, user_id=user_id)
        guest_cart = await self.get_by_session(db=db, session_id=session_id)
        
        if not guest_cart:
            if not user_cart:
                user_cart = Cart(user_id=user_id)
                db.add(user_cart)
                await db.commit()
                await db.refresh(user_cart)
            return user_cart
        
        if not user_cart:
            guest_cart.user_id = user_id
            guest_cart.session_id = None
            db.add(guest_cart)
            await db.commit()
            await db.refresh(guest_cart)
            return guest_cart
        
        max_qty_str = await system_setting.get_value(
            db=db, 
            key="cart_max_item_qty", 
            default=99
        )
        max_qty = int(max_qty_str)

        user_items_map = {item.variant_id: item for item in user_cart.items}
        
        guest_items_to_delete = []

        for guest_item in guest_cart.items:
            if guest_item.variant_id in user_items_map:
                existing_item = user_items_map[guest_item.variant_id]
                new_quantity = existing_item.quantity + guest_item.quantity
                existing_item.quantity = min(new_quantity, max_qty)
                
                guest_items_to_delete.append(guest_item)
            else:
                guest_item.cart_id = user_cart.cart_id
                user_items_map[guest_item.variant_id] = guest_item

        for item in guest_items_to_delete:
            await db.delete(item)
            
        await db.delete(guest_cart)
        await db.commit()
        
        await db.refresh(user_cart)
        return user_cart

    async def clear_cart(
        self,
        *,
        db: AsyncSession,
        cart_id: int
    ) -> Cart:
        cart = await self.get(db=db, id=cart_id)
        
        for item in cart.items:
            await db.delete(item)
        
        await db.commit()
        await db.refresh(cart)
        return cart
    

    async def remove_items_after_checkout(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        variant_ids: list[int]
    ):
        """
        Xóa những sản phẩm đã được thanh toán thành công khỏi giỏ hàng.
        """
        cart_obj = await self.get_by_user(db=db, user_id=user_id)
        if not cart_obj:
            return

        statement = (
            delete(CartItem)
            .where(CartItem.cart_id == cart_obj.cart_id)
            .where(CartItem.variant_id.in_(variant_ids))
        )
        await db.execute(statement)
        await db.commit()


    async def calculate_total(
        self,
        *,
        db: AsyncSession,
        cart_id: int
    ) -> Decimal:

        statement = (
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product)
            )
            .where(Cart.cart_id == cart_id)
        )
        result = await db.execute(statement)
        cart = result.scalar_one_or_none()
        
        if not cart:
            return Decimal("0")
        
        total = Decimal("0")
        for item in cart.items:
            if item.variant and item.variant.product:
                price = item.variant.product.sale_price or item.variant.product.base_price
                total += price * item.quantity
        
        return total

    async def get_abandoned(
        self,
        *,
        db: AsyncSession,
        hours_old: int = 24,
        limit: int = 20
    ) -> List[Cart]:
        """
        Lấy các Cart có items, chưa thanh toán và cũ hơn hours_old.
        """
        cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(hours=hours_old)
        
        statement = (
            select(Cart)
            .join(CartItem)
            .options(
                selectinload(Cart.items)
                .selectinload(CartItem.variant)
                .options(
                    selectinload(ProductVariant.product),
                    selectinload(ProductVariant.color),
                    selectinload(ProductVariant.size)
                )
            )
            .where(Cart.updated_at < cutoff_time)
            .distinct()
            .limit(limit)
        )
        
        result = await db.execute(statement)
        return result.scalars().all()


class CRUDCartItem(CRUDBase[CartItem, CartItemCreate, CartItemUpdate]):

    async def get_by_cart(
        self,
        *,
        db: AsyncSession,
        cart_id: int
    ) -> List[CartItem]:
        from app.models.product import ProductVariant
        
        statement = (
            select(CartItem)
            .options(
                selectinload(CartItem.variant).selectinload(ProductVariant.product),
                selectinload(CartItem.variant).selectinload(ProductVariant.color),
                selectinload(CartItem.variant).selectinload(ProductVariant.size)
            )
            .where(CartItem.cart_id == cart_id)
            .order_by(CartItem.added_at.desc())
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_by_cart_and_variant(
        self,
        *,
        db: AsyncSession,
        cart_id: int,
        variant_id: int
    ) -> Optional[CartItem]:
        statement = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.variant_id == variant_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def add_item(
        self,
        *,
        db: AsyncSession,
        cart_id: int,
        variant_id: int,
        quantity: int = 1
    ) -> CartItem:
        from app.crud.product import product_variant

        max_qty_str = await system_setting.get_value(
            db=db, 
            key="cart_max_item_qty", 
            default=99
        )
        max_qty = int(max_qty_str)
        
        variant = await product_variant.get(db=db, id=variant_id)
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        await db.refresh(variant, ["product"])
        if not variant.product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        available_stock = variant.stock_quantity or 0
        
        if quantity > max_qty:
             raise HTTPException(
                status_code=400,
                detail=f"Cannot add more than {max_qty} items"
            )

        existing_item = await self.get_by_cart_and_variant(
            db=db,
            cart_id=cart_id,
            variant_id=variant_id
        )
        
        if existing_item:
            new_quantity = existing_item.quantity + quantity
            
            if new_quantity > max_qty:
                 raise HTTPException(
                    status_code=400,
                    detail=f"Cart item limit exceeded ({max_qty})"
                )

            if new_quantity > available_stock:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Available: {available_stock}"
                )
            
            existing_item.quantity = new_quantity
            db.add(existing_item)
            await db.commit()
            await db.refresh(existing_item)
            return existing_item
        else:
            if quantity > available_stock:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Available: {available_stock}"
                )
            
            cart_item = CartItem(
                cart_id=cart_id,
                variant_id=variant_id,
                quantity=quantity
            )
            
            db.add(cart_item)
            await db.commit()
            await db.refresh(cart_item)
            return cart_item

    async def update_quantity(
        self,
        *,
        db: AsyncSession,
        cart_item_id: int,
        quantity: int
    ) -> CartItem:
        from app.crud.product import product_variant
        
        cart_item = await self.get(db=db, id=cart_item_id)
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        max_qty_str = await system_setting.get_value(
            db=db, 
            key="cart_max_item_qty", 
            default=99
        )
        max_qty = int(max_qty_str)
        
        if quantity > max_qty:
             raise HTTPException(
                status_code=400,
                detail=f"Cannot exceed {max_qty} items"
            )

        variant = await product_variant.get(db=db, id=cart_item.variant_id)
        available_stock = variant.stock_quantity or 0
        
        if quantity > available_stock:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {available_stock}"
            )
        
        if quantity <= 0:
            await db.delete(cart_item)
            await db.commit()
            return cart_item
        
        cart_item.quantity = quantity
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)
        return cart_item

    async def remove_item(
        self,
        *,
        db: AsyncSession,
        cart_item_id: int
    ) -> CartItem:
        cart_item = await self.get(db=db, id=cart_item_id)
        await db.delete(cart_item)
        await db.commit()
        return cart_item


class CRUDAbandonedCart(CRUDBase[AbandonedCart, AbandonedCartCreate, AbandonedCartUpdate]):

    async def create_from_cart(
        self,
        *,
        db: AsyncSession,
        cart: Cart
    ) -> AbandonedCart:
        total_items = sum(item.quantity for item in cart.items)
        total_value = Decimal("0")
        
        for item in cart.items:
            if item.variant and item.variant.product:
                price = item.variant.product.sale_price or item.variant.product.base_price
                total_value += price * item.quantity
        
        abandoned_cart = AbandonedCart(
            cart_id=cart.cart_id,
            user_id=cart.user_id,
            email=cart.user.email if cart.user else None,
            total_items=total_items,
            total_value=total_value
        )
        
        db.add(abandoned_cart)
        await db.commit()
        await db.refresh(abandoned_cart)
        return abandoned_cart

    async def get_pending_reminders(
        self,
        *,
        db: AsyncSession,
        hours_since_abandon: int = 0,
        limit: int = 100
    ) -> List[AbandonedCart]:
        
        if hours_since_abandon > 0:
            hours = hours_since_abandon
        else:
            delay_str = await system_setting.get_value(
                db=db, 
                key="abandoned_cart_delay_hours", 
                default=2
            )
            hours = int(delay_str)

        max_emails_str = await system_setting.get_value(
            db=db, 
            key="max_abandoned_cart_emails", 
            default=3
        )
        max_emails = int(max_emails_str)
       
        cutoff_time = datetime.now(timezone(timedelta(hours=7))) - timedelta(hours=hours)
        
        statement = (
            select(AbandonedCart)
            .where(
                AbandonedCart.created_at < cutoff_time,
                AbandonedCart.email_sent_count < max_emails,
                AbandonedCart.recovered == False
            )
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def mark_email_sent(
        self,
        *,
        db: AsyncSession,
        abandoned_cart_id: int
    ) -> AbandonedCart:
        abandoned_cart = await self.get(db=db, id=abandoned_cart_id)
        abandoned_cart.email_sent_count += 1
        abandoned_cart.last_email_sent = datetime.now(timezone(timedelta(hours=7)))
        
        db.add(abandoned_cart)
        await db.commit()
        await db.refresh(abandoned_cart)
        return abandoned_cart

    async def mark_recovered(
        self,
        *,
        db: AsyncSession,
        abandoned_cart_id: int
    ) -> AbandonedCart:
        abandoned_cart = await self.get(db=db, id=abandoned_cart_id)
        abandoned_cart.recovered = True
        abandoned_cart.recovered_at = datetime.now(timezone(timedelta(hours=7)))
        
        db.add(abandoned_cart)
        await db.commit()
        await db.refresh(abandoned_cart)
        return abandoned_cart


cart = CRUDCart(Cart)
cart_item = CRUDCartItem(CartItem)
abandoned_cart = CRUDAbandonedCart(AbandonedCart)