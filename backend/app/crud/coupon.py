from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.coupon import (
    Coupon,
    CouponCreate,
    CouponUpdate,
    CouponValidationResult,
    OrderCoupon,
    OrderCouponCreate,
    FlashSale,
    FlashSaleCreate,
    FlashSaleUpdate,
    FlashSaleProduct,
    FlashSaleProductCreate,
)
from app.models.enums import DiscountTypeEnum
from app.crud.system import system_setting


class CRUDCoupon(CRUDBase[Coupon, CouponCreate, CouponUpdate]):

    async def get_by_code(
        self,
        *,
        db: AsyncSession,
        code: str
    ) -> Optional[Coupon]:
        statement = select(Coupon).where(Coupon.coupon_code == code)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_active(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Coupon]:
        now = datetime.now(timezone(timedelta(hours=7)))
        
        statement = (
            select(Coupon)
            .where(
                Coupon.is_active.is_(True),
                or_(
                    Coupon.start_date.is_(None),
                    Coupon.start_date <= now
                ),
                or_(
                    Coupon.end_date.is_(None),
                    Coupon.end_date >= now
                )
            )
            .order_by(Coupon.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def validate_coupon(
        self,
        *,
        db: AsyncSession,
        code: str,
        user_id: Optional[int] = None,
        order_amount: Decimal = Decimal("0.00")
    ) -> CouponValidationResult:
        coupon = await self.get_by_code(db=db, code=code)
        
        if not coupon:
            return CouponValidationResult(
                valid=False,
                discount_amount=Decimal("0.00"),
                error="Coupon not found"
            )
        
        if not coupon.is_active:
            return CouponValidationResult(
                valid=False,
                discount_amount=Decimal("0.00"),
                error="Coupon is not active"
            )
        
        now = datetime.now(timezone(timedelta(hours=7)))
        if coupon.start_date and now < coupon.start_date:
            return CouponValidationResult(
                valid=False,
                discount_amount=Decimal("0.00"),
                error="Coupon not yet valid"
            )
        
        if coupon.end_date and now > coupon.end_date:
            return CouponValidationResult(
                valid=False,
                discount_amount=Decimal("0.00"),
                error="Coupon has expired"
            )

        if coupon.customer_eligibility:
            elig_value = coupon.customer_eligibility.strip().upper()

            if elig_value == "ALL":
                pass 
            
            elif elig_value.isdigit():
                if not user_id or int(elig_value) != user_id:
                    return CouponValidationResult(
                        valid=False,
                        discount_amount=Decimal("0.00"),
                        error="Mã giảm giá này đã được cấp riêng cho một tài khoản khác."
                    )

            elif elig_value in ["BRONZE", "SILVER", "GOLD", "DIAMOND"]:
                from app.crud.loyalty import loyalty_point_crud
                user_loyalty = await loyalty_point_crud.get_by_user(db=db, user_id=user_id)
                
                current_tier = user_loyalty.tier.tier_name.upper() if user_loyalty and user_loyalty.tier else "BRONZE"
                
                if current_tier != elig_value:
                    return CouponValidationResult(
                        valid=False,
                        discount_amount=Decimal("0.00"),
                        error=f"Mã này chỉ dành cho thành viên hạng {elig_value}."
                    )
        
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return CouponValidationResult(
                valid=False,
                discount_amount=Decimal("0.00"),
                error="Coupon usage limit reached"
            )
        
        if user_id:
            usage_stmt = select(func.count(OrderCoupon.order_coupon_id)).join(
                OrderCoupon.order
            ).where(
                OrderCoupon.coupon_id == coupon.coupon_id,
                OrderCoupon.order.has(user_id=user_id) 
            )
            usage_result = await db.execute(usage_stmt)
            user_usage_count = usage_result.scalar_one()

            max_usage_str = await system_setting.get_value(
                db=db, 
                key="max_coupon_usage_per_user", 
                default=1
            )
            max_usage = int(max_usage_str)
            
            if user_usage_count >= max_usage:
                return CouponValidationResult(
                    valid=False,
                    discount_amount=Decimal("0.00"),
                    error=f"You have reached the usage limit ({max_usage}) for this coupon"
                )

        if order_amount < coupon.min_purchase_amount:
            return CouponValidationResult(
                valid=False,
                discount_amount=Decimal("0.00"),
                error=f"Minimum purchase amount is {coupon.min_purchase_amount:,.0f} VND"
            )
        
        if coupon.discount_type == DiscountTypeEnum.PERCENTAGE:
            discount_amount = order_amount * (coupon.discount_value / 100)
        elif coupon.discount_type == DiscountTypeEnum.FIXED_AMOUNT:
            discount_amount = coupon.discount_value
        else:
            discount_amount = Decimal("0.00")
        
        if coupon.max_discount_amount and discount_amount > coupon.max_discount_amount:
            discount_amount = coupon.max_discount_amount
        
        if discount_amount > order_amount:
            discount_amount = order_amount
        
        return CouponValidationResult(
            valid=True,
            discount_amount=discount_amount,
            coupon=coupon
        )


    async def get_public_coupons(
        self,
        *,
        db: AsyncSession,
        limit: int = 10
    ) -> List[Coupon]:
        now = datetime.now(timezone(timedelta(hours=7)))
        
        statement = (
            select(Coupon)
            .where(
                Coupon.is_active.is_(True),
                or_(
                    Coupon.start_date.is_(None),
                    Coupon.start_date <= now
                ),
                or_(
                    Coupon.end_date.is_(None),
                    Coupon.end_date >= now
                ),
                Coupon.customer_eligibility.ilike("ALL"),
                
                or_(
                    Coupon.usage_limit.is_(None),
                    Coupon.used_count < Coupon.usage_limit
                )
            )
            .order_by(Coupon.discount_value.desc())
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())


    async def get_coupons_for_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        user_tier: str,
        limit: int = 50
    ) -> List[Coupon]:
        """
        Lấy mã cho ví Voucher: Public + Hạng + Riêng tư.
        Loại bỏ mã đã hết hạn và mã user đã sử dụng.
        """

        from app.models.order import Order
        from app.models.enums import OrderStatusEnum

        now = datetime.now(timezone(timedelta(hours=7)))
        user_id_str = str(user_id)
        
        subquery = (
            select(OrderCoupon.coupon_id)
            .join(OrderCoupon.order)
            .where(
                OrderCoupon.order.has(user_id=user_id),
                OrderCoupon.order.has(Order.order_status != OrderStatusEnum.CANCELLED)
            )
        )

        statement = (
            select(Coupon)
            .where(
                Coupon.is_active.is_(True),
                or_(Coupon.start_date.is_(None), Coupon.start_date <= now),
                or_(Coupon.end_date.is_(None), Coupon.end_date >= now),
                
                or_(
                    Coupon.customer_eligibility.ilike("ALL"),
                    Coupon.customer_eligibility == user_tier,
                    Coupon.customer_eligibility == user_id_str
                ),
                

                Coupon.coupon_id.not_in(subquery),
                
                or_(
                    Coupon.usage_limit.is_(None),
                    Coupon.used_count < Coupon.usage_limit
                )
            )
            .order_by(Coupon.end_date.asc())
            .limit(limit)
        )
        
        result = await db.execute(statement)
        return list(result.scalars().all())


class CRUDOrderCoupon(CRUDBase[OrderCoupon, OrderCouponCreate, Dict[str, Any]]):

    async def get_by_order(
        self,
        *,
        db: AsyncSession,
        order_id: int
    ) -> List[OrderCoupon]:
        statement = (
            select(OrderCoupon)
            .options(selectinload(OrderCoupon.coupon))
            .where(OrderCoupon.order_id == order_id)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def create_for_order(
        self,
        *,
        db: AsyncSession,
        order_id: int,
        coupon_id: int
    ) -> OrderCoupon:
        order_coupon = OrderCoupon(
            order_id=order_id,
            coupon_id=coupon_id
        )
        db.add(order_coupon)
        await db.commit()
        await db.refresh(order_coupon)
        return order_coupon


class CRUDFlashSale(CRUDBase[FlashSale, FlashSaleCreate, FlashSaleUpdate]):

    async def get_active(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[FlashSale]:
        now = datetime.now(timezone(timedelta(hours=7)))
        
        statement = (
            select(FlashSale)
            .options(selectinload(FlashSale.flash_sale_products))
            .where(
                FlashSale.is_active.is_(True),
                FlashSale.start_time <= now,
                FlashSale.end_time >= now
            )
            .order_by(FlashSale.start_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        sales = list(result.scalars().all())
        
        for sale in sales:
            sale.product_count = len(sale.flash_sale_products)
            
        return sales

    async def get_upcoming(
        self,
        *,
        db: AsyncSession,
        limit: int = 10
    ) -> List[FlashSale]:
        now = datetime.now(timezone(timedelta(hours=7)))
        
        statement = (
            select(FlashSale)
            .options(selectinload(FlashSale.flash_sale_products))
            .where(
                FlashSale.is_active.is_(True),
                FlashSale.start_time > now
            )
            .order_by(FlashSale.start_time)
            .limit(limit)
        )
        result = await db.execute(statement)
        sales = list(result.scalars().all())
        
        for sale in sales:
            sale.product_count = len(sale.flash_sale_products)
            
        return sales

    async def get_with_products(
        self,
        *,
        db: AsyncSession,
        flash_sale_id: int
    ) -> Optional[FlashSale]:
        
        from app.models.product import Product

        statement = (
            select(FlashSale)
            .options(
                selectinload(FlashSale.flash_sale_products)
                .selectinload(FlashSaleProduct.product)
                .selectinload(Product.images)
            )
            .where(FlashSale.flash_sale_id == flash_sale_id)
        )
        result = await db.execute(statement)
        flash_sale = result.scalar_one_or_none()

        if not flash_sale:
            return None

        products = [
            {
                "flash_sale_product_id": fsp.flash_sale_product_id,
                "quantity_limit": fsp.quantity_limit,
                "quantity_sold": fsp.quantity_sold,
                "product_id": fsp.product.product_id,
                "product_name": fsp.product.product_name, 
                "slug": fsp.product.slug,
                "price": float(fsp.product.base_price) if fsp.product.base_price else 0.0,
                "images": fsp.product.images if fsp.product.images else [],
            }
            for fsp in flash_sale.flash_sale_products
            if fsp.product
        ]

        data = flash_sale.model_dump()
        data["products"] = products
        
        return data

    async def check_active_for_product(
        self,
        *,
        db: AsyncSession,
        product_id: int
    ) -> Optional[FlashSale]:
        now = datetime.now(timezone(timedelta(hours=7)))
        
        statement = (
            select(FlashSale)
            .join(FlashSaleProduct)
            .where(
                FlashSale.is_active.is_(True),
                FlashSale.start_time <= now,
                FlashSale.end_time >= now,
                FlashSaleProduct.product_id == product_id
            )
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()


class CRUDFlashSaleProduct(CRUDBase[FlashSaleProduct, FlashSaleProductCreate, Dict[str, Any]]):

    async def get_by_flash_sale(
        self,
        *,
        db: AsyncSession,
        flash_sale_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[FlashSaleProduct]:
        statement = (
            select(FlashSaleProduct)
            .options(selectinload(FlashSaleProduct.product))
            .where(FlashSaleProduct.flash_sale_id == flash_sale_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def add_product(
        self,
        *,
        db: AsyncSession,
        flash_sale_id: int,
        product_id: int,
        quantity_limit: Optional[int] = None
    ) -> FlashSaleProduct:
        statement = select(FlashSaleProduct).where(
            FlashSaleProduct.flash_sale_id == flash_sale_id,
            FlashSaleProduct.product_id == product_id
        )
        result = await db.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        flash_sale_product = FlashSaleProduct(
            flash_sale_id=flash_sale_id,
            product_id=product_id,
            quantity_limit=quantity_limit,
            quantity_sold=0
        )
        db.add(flash_sale_product)
        await db.commit()
        await db.refresh(flash_sale_product)
        return flash_sale_product

    async def remove_product(
        self,
        *,
        db: AsyncSession,
        flash_sale_id: int,
        product_id: int
    ) -> bool:
        statement = select(FlashSaleProduct).where(
            FlashSaleProduct.flash_sale_id == flash_sale_id,
            FlashSaleProduct.product_id == product_id
        )
        result = await db.execute(statement)
        flash_sale_product = result.scalar_one_or_none()
        
        if not flash_sale_product:
            return False
        
        await db.delete(flash_sale_product)
        await db.commit()
        return True

    async def increment_sold(
        self,
        *,
        db: AsyncSession,
        flash_sale_id: int,
        product_id: int,
        quantity: int = 1
    ) -> bool:
        statement = (
            update(FlashSaleProduct)
            .where(
                FlashSaleProduct.flash_sale_id == flash_sale_id,
                FlashSaleProduct.product_id == product_id
            )
            .values(quantity_sold=FlashSaleProduct.quantity_sold + quantity)
        )
        result = await db.execute(statement)
        await db.commit()
        
        return result.rowcount > 0

    async def check_availability(
        self,
        *,
        db: AsyncSession,
        flash_sale_id: int,
        product_id: int,
        requested_quantity: int = 1
    ) -> tuple[bool, Optional[str]]:
        statement = select(FlashSaleProduct).where(
            FlashSaleProduct.flash_sale_id == flash_sale_id,
            FlashSaleProduct.product_id == product_id
        )
        result = await db.execute(statement)
        flash_sale_product = result.scalar_one_or_none()
        
        if not flash_sale_product:
            return False, "Product not in flash sale"
        
        if not flash_sale_product.quantity_limit:
            return True, None
        
        remaining = flash_sale_product.quantity_limit - flash_sale_product.quantity_sold
        
        if remaining < requested_quantity:
            return False, f"Only {remaining} items remaining"
        
        return True, None


coupon = CRUDCoupon(Coupon)
order_coupon = CRUDOrderCoupon(OrderCoupon)
flash_sale = CRUDFlashSale(FlashSale)
flash_sale_product = CRUDFlashSaleProduct(FlashSaleProduct)