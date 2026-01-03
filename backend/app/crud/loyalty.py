from typing import List, Optional
from datetime import datetime, timezone, timedelta
import secrets
import string
from decimal import Decimal

from app.models.coupon import Coupon
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.crud.base import CRUDBase
from app.models.loyalty import (
    LoyaltyTier,
    LoyaltyTierCreate,
    LoyaltyTierUpdate,
    LoyaltyPoint,
    LoyaltyPointCreate,
    LoyaltyPointUpdate,
    PointTransaction,
    PointTransactionCreate,
    Referral,
    ReferralCreate,
    ReferralUpdate,
)
from app.models.enums import DiscountTypeEnum, LoyaltyTransactionEnum
from app.crud.system import system_setting


class CRUDLoyaltyTier(CRUDBase[LoyaltyTier, LoyaltyTierCreate, LoyaltyTierUpdate]):
    """CRUD operations cho LoyaltyTier"""

    async def get_active_tiers(
        self,
        *,
        db: AsyncSession
    ) -> List[LoyaltyTier]:
        statement = (
            select(LoyaltyTier)
            .where(LoyaltyTier.is_active == True)
            .order_by(LoyaltyTier.min_points)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_tier_for_points(
        self,
        *,
        db: AsyncSession,
        points: int
    ) -> Optional[LoyaltyTier]:
        statement = (
            select(LoyaltyTier)
            .where(
                LoyaltyTier.is_active == True,
                LoyaltyTier.min_points <= points
            )
            .order_by(LoyaltyTier.min_points.desc())
        )
        result = await db.execute(statement)
        return result.scalars().first()


class CRUDLoyaltyPoint(CRUDBase[LoyaltyPoint, LoyaltyPointCreate, LoyaltyPointUpdate]):
    """CRUD operations cho LoyaltyPoint"""

    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int
    ) -> Optional[LoyaltyPoint]:
        statement = (
            select(LoyaltyPoint)
            .options(selectinload(LoyaltyPoint.tier))
            .where(LoyaltyPoint.user_id == user_id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        db: AsyncSession,
        user_id: int
    ) -> LoyaltyPoint:
        loyalty = await self.get_by_user(db=db, user_id=user_id)
        
        if not loyalty:
            default_tier = await loyalty_tier_crud.get_tier_for_points(db=db, points=0)
            
            loyalty = LoyaltyPoint(
                user_id=user_id,
                points_balance=0,
                total_earned=0,
                total_spent=0,
                tier_id=default_tier.tier_id if default_tier else None
            )
            db.add(loyalty)
            await db.commit()
            await db.refresh(loyalty)
        
        return loyalty

    async def earn_points(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        points: int,
        transaction_type: LoyaltyTransactionEnum,
        description: str,
        order_id: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> LoyaltyPoint:
        
        from app.crud.loyalty import loyalty_tier_crud

        if points <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Points must be positive"
            )
        
        if expires_at is None:
            days_str = await system_setting.get_value(db=db, key="point_expiration_days", default="365")
            try:
                days = int(days_str)
            except ValueError:
                days = 365

            expires_at = datetime.now(timezone(timedelta(hours=7))) + timedelta(days=days)
        
        loyalty = await self.get_or_create(db=db, user_id=user_id)
        
        loyalty.points_balance += points
        loyalty.total_earned += points
        
        new_tier = await loyalty_tier_crud.get_tier_for_points(
            db=db,
            points=loyalty.total_earned
        )
        if new_tier:
            loyalty.tier_id = new_tier.tier_id
        
        db.add(loyalty)
        
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            points=points,
            order_id=order_id,
            description=description,
            expires_at=expires_at
        )
        db.add(transaction)
        
        await db.commit()
        await db.refresh(loyalty)
        
        return loyalty

    async def spend_points(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        points: int,
        description: str,
        order_id: Optional[int] = None
    ) -> LoyaltyPoint:
        if points <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Points must be positive"
            )
        
        loyalty = await self.get_by_user(db=db, user_id=user_id)
        
        if not loyalty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Loyalty account not found"
            )
        
        if loyalty.points_balance < points:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient points. Available: {loyalty.points_balance}"
            )
        
        loyalty.points_balance -= points
        loyalty.total_spent += points
        
        db.add(loyalty)
        
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=LoyaltyTransactionEnum.REDEEM,
            points=-points,
            order_id=order_id,
            description=description
        )
        db.add(transaction)
        
        await db.commit()
        await db.refresh(loyalty)
        
        return loyalty

    async def adjust_points(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        points: int,
        description: str
    ) -> LoyaltyPoint:
        loyalty = await self.get_or_create(db=db, user_id=user_id)
        
        loyalty.points_balance += points
        
        if loyalty.points_balance < 0:
            loyalty.points_balance = 0
        
        if points > 0:
            loyalty.total_earned += points
        else:
            loyalty.total_spent += abs(points)
        
        new_tier = await loyalty_tier_crud.get_tier_for_points(
            db=db,
            points=loyalty.total_earned
        )
        if new_tier:
            loyalty.tier_id = new_tier.tier_id
        
        db.add(loyalty)
        
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=LoyaltyTransactionEnum.ADJUSTMENT,
            points=points,
            description=f"Admin adjustment: {description}"
        )
        db.add(transaction)
        
        await db.commit()
        await db.refresh(loyalty)
        
        return loyalty

    async def get_leaderboard(
        self,
        *,
        db: AsyncSession,
        limit: int = 100
    ) -> List[LoyaltyPoint]:
        statement = (
            select(LoyaltyPoint)
            .options(
                selectinload(LoyaltyPoint.user),
                selectinload(LoyaltyPoint.tier)
            )
            .order_by(LoyaltyPoint.total_earned.desc())
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def process_order_earning(
        self,
        *,
        db: AsyncSession,
        order_id: int,
        user_id: int,
        total_amount: Decimal
    ) -> Optional[LoyaltyPoint]:
        """
        Tự động tính và cộng điểm khi đơn hàng hoàn tất (COMPLETED).
        Lấy tỷ lệ đổi điểm từ Database (Admin cấu hình).
        """
        stmt = select(PointTransaction).where(
            PointTransaction.source_type == "ORDER",
            PointTransaction.order_id == order_id,
            PointTransaction.transaction_type == LoyaltyTransactionEnum.EARN_PURCHASE
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return None 

        rate_str = await system_setting.get_value(db=db, key="loyalty_exchange_rate", default="100")
        try:
            exchange_rate = int(rate_str)
        except ValueError:
            exchange_rate = 10000
        
        if exchange_rate <= 0:
            exchange_rate = 10000

        points = int(total_amount / exchange_rate)
        
        if points <= 0:
            return None

        return await self.earn_points(
            db=db,
            user_id=user_id,
            points=points,
            transaction_type=LoyaltyTransactionEnum.EARN_PURCHASE,
            description=f"Thưởng mua hàng đơn #{order_id}",
            order_id=order_id
        )
    
    async def redeem_points_to_coupon(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        discount_value: int,
    ) -> Coupon:
        loyalty = await self.get_by_user(db=db, user_id=user_id)
        if not loyalty or not loyalty.tier:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông tin hạng thành viên")
        
        rate_str = await system_setting.get_value(db=db, key="redeem_point_exchange_rate", default="1")
        exchange_rate = int(rate_str)
        points_to_redeem = discount_value
        real_money_amount = points_to_redeem * exchange_rate

        tier_name = loyalty.tier.tier_name.strip().replace(" ", "").lower()
        limit_key = f"redeem_limit_{tier_name}"
        max_limit_str = await system_setting.get_value(db=db, key=limit_key, default="1")

        if real_money_amount > int(max_limit_str) and int(max_limit_str) > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Hạng {tier_name.upper()} chỉ được đổi tối đa {int(max_limit_str):,.0f} VNĐ"
            )

        if loyalty.points_balance < points_to_redeem:
            raise HTTPException(status_code=400, detail="Bạn không đủ điểm để đổi voucher này")

        value_tag = f"{discount_value // 1000}K"
        random_suffix = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        coupon_code = f"{tier_name.upper()}{value_tag}{random_suffix}"

        valid_days_str = await system_setting.get_value(db=db, key="redeem_coupon_validity_days", default="30")
        expiry_date = datetime.now(timezone(timedelta(hours=7))) + timedelta(days=int(valid_days_str))

        new_coupon = Coupon(
            coupon_code=coupon_code,
            discount_type=DiscountTypeEnum.FIXED_AMOUNT,
            discount_value=Decimal(real_money_amount),
            usage_limit=1,
            customer_eligibility=str(user_id),
            start_date=datetime.now(timezone(timedelta(hours=7))),
            end_date=expiry_date,
            is_active=True,
            description=f"Voucher đổi từ điểm thưởng của {tier_name.upper()}"
        )
        db.add(new_coupon)

        await self.spend_points(
            db=db,
            user_id=user_id,
            points=points_to_redeem,
            description=f"Đổi điểm lấy mã Coupon: {coupon_code}"
        )
        
        await db.commit()
        await db.refresh(new_coupon)
        return new_coupon


class CRUDPointTransaction(CRUDBase[PointTransaction, PointTransactionCreate, dict]):
    """CRUD operations cho PointTransaction"""
    
    async def get_by_user(
        self,
        *,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[PointTransaction]:
        statement = (
            select(PointTransaction)
            .where(PointTransaction.user_id == user_id)
            .order_by(PointTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def expire_old_points(
        self,
        *,
        db: AsyncSession
    ) -> int:
        now = datetime.now(timezone(timedelta(hours=7)))
        
        statement = select(PointTransaction).where(
            PointTransaction.expires_at < now,
            PointTransaction.points > 0
        )
        result = await db.execute(statement)
        expired_transactions = result.scalars().all()
        
        affected_users = set()
        
        for transaction in expired_transactions:
            loyalty = await loyalty_point_crud.get_by_user(
                db=db,
                user_id=transaction.user_id
            )
            
            if loyalty and loyalty.points_balance > 0:
                points_to_expire = min(loyalty.points_balance, transaction.points)
                
                if points_to_expire > 0:
                    loyalty.points_balance -= points_to_expire
                    db.add(loyalty)
                    expiry = PointTransaction(
                        user_id=transaction.user_id,
                        transaction_type=LoyaltyTransactionEnum.EXPIRE,
                        points=-points_to_expire,
                        description=f"Expired points from {transaction.created_at.date()}"
                    )
                    db.add(expiry)
                    
                    affected_users.add(transaction.user_id)
                    transaction.points = 0 
                    db.add(transaction)
        
        await db.commit()
        return len(affected_users)


class CRUDReferral(CRUDBase[Referral, ReferralCreate, ReferralUpdate]):
    """CRUD operations cho Referral"""
    
    async def get_by_code(
        self,
        *,
        db: AsyncSession,
        code: str
    ) -> Optional[Referral]:
        statement = (
            select(Referral)
            .options(
                selectinload(Referral.referrer),
                selectinload(Referral.referred_user)
            )
            .where(Referral.referral_code == code)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_referrer(
        self,
        *,
        db: AsyncSession,
        referrer_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Referral]:
        statement = (
            select(Referral)
            .options(selectinload(Referral.referred_user))
            .where(Referral.referrer_id == referrer_id)
            .order_by(Referral.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def create_referral(
        self,
        *,
        db: AsyncSession,
        referrer_id: int,
        referred_user_id: int,
        referral_code: str,
        reward_points: Optional[int] = None
    ) -> Referral:
        if reward_points is None:
            points_str = await system_setting.get_value(db=db, key="referral_reward_points", default="200")
            try:
                reward_points = int(points_str)
            except ValueError:
                reward_points = 200

        referral = Referral(
            referrer_id=referrer_id,
            referred_user_id=referred_user_id,
            referral_code=referral_code,
            reward_points=reward_points,
            is_rewarded=False
        )
        
        db.add(referral)
        await db.commit()
        await db.refresh(referral)
        
        return referral

    async def reward_referral(
        self,
        *,
        db: AsyncSession,
        referral_id: int
    ) -> Referral:
        
        from app.crud.loyalty import loyalty_point_crud

        referral = await self.get(db=db, id=referral_id)
        
        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referral not found"
            )
        
        if referral.is_rewarded:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Referral already rewarded"
            )
        
        await loyalty_point_crud.earn_points(
            db=db,
            user_id=referral.referrer_id,
            points=referral.reward_points,
            transaction_type=LoyaltyTransactionEnum.EARN_REFERRAL,
            description=f"Referral reward for inviting user {referral.referred_user_id}"
        )
        
        referral.is_rewarded = True
        referral.rewarded_at = datetime.now(timezone(timedelta(hours=7)))
        
        db.add(referral)
        await db.commit()
        await db.refresh(referral)
        
        return referral

    async def get_referral_stats(
        self,
        *,
        db: AsyncSession,
        referrer_id: int
    ) -> dict:
        total_stmt = select(func.count(Referral.referral_id)).where(
            Referral.referrer_id == referrer_id
        )
        total_result = await db.execute(total_stmt)
        total = total_result.scalar_one()
        
        rewarded_stmt = select(func.count(Referral.referral_id)).where(
            Referral.referrer_id == referrer_id,
            Referral.is_rewarded == True
        )
        rewarded_result = await db.execute(rewarded_stmt)
        rewarded = rewarded_result.scalar_one()
        
        points_stmt = select(func.sum(Referral.reward_points)).where(
            Referral.referrer_id == referrer_id,
            Referral.is_rewarded == True
        )
        points_result = await db.execute(points_stmt)
        total_points = points_result.scalar_one() or 0
        
        return {
            "total_referrals": total,
            "rewarded_referrals": rewarded,
            "pending_referrals": total - rewarded,
            "total_points_earned": total_points
        }
    
    async def process_instant_referral(
        self,
        *,
        db: AsyncSession,
        referrer_code: str,
        new_user_id: int,
        is_email_verified: bool
    ) -> tuple[bool, str]:
        from app.models.user import User
        from app.crud.loyalty import loyalty_point_crud

        if not is_email_verified:
            return False, "Bạn cần xác thực email trước khi thực hiện thao tác này."

        stmt = select(User).where(User.referral_code == referrer_code)
        referrer = (await db.execute(stmt)).scalar_one_or_none()
        
        if not referrer:
            return False, "Mã giới thiệu không tồn tại."
            
        if referrer.user_id == new_user_id:
            return False, "Bạn không thể nhập mã của chính mình."

        check_stmt = select(Referral).where(Referral.referred_user_id == new_user_id)
        existing = (await db.execute(check_stmt)).first()
        if existing:
            return False, "Bạn đã nhận quà giới thiệu trước đó rồi."

        try:
            referrer_points_str = await system_setting.get_value(db=db, key="referral_reward_points", default="200")
            referrer_points = int(referrer_points_str)

            referee_points_str = await system_setting.get_value(db=db, key="referee_reward_points", default="100")
            referee_points = int(referee_points_str)

            await loyalty_point_crud.earn_points(
                db=db,
                user_id=referrer.user_id,
                points=referrer_points,
                transaction_type=LoyaltyTransactionEnum.EARN_REFERRAL,
                description=f"Thưởng giới thiệu bạn mới (ID: {new_user_id})"
            )

            await loyalty_point_crud.earn_points(
                db=db,
                user_id=new_user_id,
                points=referee_points,
                transaction_type=LoyaltyTransactionEnum.EARN_REFERRAL,
                description=f"Quà tặng nhập mã giới thiệu từ {referrer_code}"
            )

            new_ref = Referral(
                referrer_id=referrer.user_id,
                referred_user_id=new_user_id,
                referral_code=referrer_code,
                reward_points=referrer_points,
                is_rewarded=True,
                rewarded_at=datetime.now(timezone(timedelta(hours=7)))
            )
            db.add(new_ref)
            
            await db.commit()
            return True, f"Nhập mã thành công! Bạn nhận được {referee_points} điểm."
            
        except Exception as e:
            await db.rollback()
            return False, f"Lỗi hệ thống: {str(e)}"

loyalty_tier_crud = CRUDLoyaltyTier(LoyaltyTier)
loyalty_point_crud = CRUDLoyaltyPoint(LoyaltyPoint)
point_transaction_crud = CRUDPointTransaction(PointTransaction)
referral_crud = CRUDReferral(Referral)