from typing import Any, List

from fastapi import APIRouter, Body, Query, status, HTTPException, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

from app.api.deps import (
    SessionDep,
    CurrentUser,
    require_permission,
)
from app.crud.loyalty import (
    loyalty_tier_crud,
    loyalty_point_crud,
    point_transaction_crud,
    referral_crud,
)
from app.models.loyalty import (
    LoyaltyTierResponse,
    LoyaltyTierCreate,
    LoyaltyTierUpdate,
    LoyaltyPointResponse,
    PointTransactionResponse,
    ReferralResponse,
    EarnPointsRequest,
    RedeemPointsRequest,
    ReferralRewardRequest,
)
from app.models.coupon import CouponResponse
from app.models.enums import LoyaltyTransactionEnum
from app.models.common import Message
from app.models.user import User
from app.crud.system import system_setting

router = APIRouter()


@router.get("/tiers", response_model=List[LoyaltyTierResponse])
@cache(expire=3600, namespace="loyalty-tiers")
async def list_loyalty_tiers(
    db: SessionDep,
) -> List[LoyaltyTierResponse]:
    """
    Lấy danh sách tất cả các hạng thành viên (Tiers) đang hoạt động.
    """
    tiers = await loyalty_tier_crud.get_active_tiers(db=db)
    return tiers


@router.get("/me", response_model=LoyaltyPointResponse)
async def get_my_points(
    db: SessionDep,
    current_user: CurrentUser,
) -> LoyaltyPointResponse:
    """
    Lấy thông tin điểm thưởng và hạng thành viên hiện tại của người dùng.
    """
    loyalty = await loyalty_point_crud.get_or_create(
        db=db,
        user_id=current_user.user_id
    )
    
    return LoyaltyPointResponse(
        loyalty_id=loyalty.loyalty_id,
        user_id=loyalty.user_id,
        points_balance=loyalty.points_balance,
        total_earned=loyalty.total_earned,
        total_spent=loyalty.total_spent,
        tier_id=loyalty.tier_id,
        created_at=loyalty.created_at,
        updated_at=loyalty.updated_at,
        tier={
            "tier_id": loyalty.tier.tier_id,
            "tier_name": loyalty.tier.tier_name,
            "min_points": loyalty.tier.min_points,
            "discount_percentage": float(loyalty.tier.discount_percentage),
            "benefits": loyalty.tier.benefits
        } if loyalty.tier else None
    )


@router.get("/transactions", response_model=List[PointTransactionResponse])
async def get_my_transactions(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[PointTransactionResponse]:
    """
    Xem lịch sử các giao dịch tích điểm hoặc tiêu điểm của người dùng hiện tại.
    """
    transactions = await point_transaction_crud.get_by_user(
        db=db,
        user_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    return transactions


@router.post("/redeem", response_model=CouponResponse)
async def redeem_points(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    redeem_data: RedeemPointsRequest,
) -> Any:
    """
    Thực hiện quy đổi điểm thưởng sang mã Coupon cá nhân (Tier-Based).
    """
    new_coupon = await loyalty_point_crud.redeem_points_to_coupon(
        db=db,
        user_id=current_user.user_id,
        discount_value=int(redeem_data.points)
    )
    
    return new_coupon


@router.get("/leaderboard", response_model=List[dict])
@cache(expire=1800, namespace="loyalty-leaderboard")
async def get_leaderboard(
    db: SessionDep,
    limit: int = Query(100, ge=1, le=100),
) -> List[dict]:
    """
    Lấy bảng xếp hạng người dùng dựa trên tổng số điểm thưởng tích lũy.
    """
    leaderboard = await loyalty_point_crud.get_leaderboard(db=db, limit=limit)
    
    return [
        {
            "rank": idx + 1,
            "user": {
                "user_id": loyalty.user.user_id,
                "first_name": loyalty.user.first_name,
                "last_name": loyalty.user.last_name,
            } if loyalty.user else None,
            "points": loyalty.total_earned,
            "tier": {
                "tier_name": loyalty.tier.tier_name
            } if loyalty.tier else None
        }
        for idx, loyalty in enumerate(leaderboard)
    ]


@router.get("/referrals/my-code", response_model=dict)
async def get_my_referral_code(
    db: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Lấy mã giới thiệu và đường dẫn giới thiệu cá nhân của người dùng.
    """
    code = current_user.referral_code
    
    if not code:
        code = "CONTACT-SUPPORT" 
        
    reward_points_str = await system_setting.get_value(db=db, key="referral_reward_points", default="200")
        
    return {
        "referral_code": code,
        "referral_url": f"https://yourstore.com/register?ref={code}",
        "reward_points": int(reward_points_str)
    }


@router.get("/referrals/my-referrals", response_model=List[ReferralResponse])
async def get_my_referrals(
    db: SessionDep,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> List[ReferralResponse]:
    """
    Xem danh sách những người dùng đã đăng ký thông qua mã giới thiệu của mình.
    """
    referrals = await referral_crud.get_by_referrer(
        db=db,
        referrer_id=current_user.user_id,
        skip=skip,
        limit=limit
    )
    
    return [
        ReferralResponse(
            referral_id=ref.referral_id,
            referrer_id=ref.referrer_id,
            referred_user_id=ref.referred_user_id,
            referral_code=ref.referral_code,
            reward_points=ref.reward_points,
            is_rewarded=ref.is_rewarded,
            rewarded_at=ref.rewarded_at,
            created_at=ref.created_at,
            referred_user={
                "user_id": ref.referred_user.user_id,
                "first_name": ref.referred_user.first_name,
                "last_name": ref.referred_user.last_name,
                "email": ref.referred_user.email,
            } if ref.referred_user else None
        )
        for ref in referrals
    ]


@router.get("/referrals/stats", response_model=dict)
async def get_my_referral_stats(
    db: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Xem các số liệu thống kê về kết quả giới thiệu người dùng mới.
    """
    stats = await referral_crud.get_referral_stats(
        db=db,
        referrer_id=current_user.user_id
    )
    return stats


@router.get("/referrals/status", response_model=dict)
async def get_referral_status(
    db: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """
    Dùng cho màn hình Giới thiệu trong Setting.
    Kiểm tra bảng Referral để quyết định hiện/ẩn ô nhập mã.
    """
    from app.models.loyalty import Referral
    from sqlalchemy import select

    stmt = select(Referral).where(Referral.referred_user_id == current_user.user_id)
    result = await db.execute(stmt)
    referral_record = result.scalar().one_or_none()

    return {
        "my_referral_code": current_user.referral_code,
        "can_claim": referral_record is None,
        "is_verified": current_user.is_email_verified
    }


@router.post("/referrals/claim", response_model=Message)
async def claim_referral(
    *,
    db: SessionDep,
    current_user: CurrentUser,
    referral_code: str = Body(..., embed=True),
) -> Message:
    """
    Xử lý nhập mã giới thiệu và cộng điểm ngay lập tức.
    """
    if not current_user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bạn cần xác thực email trước khi nhập mã giới thiệu."
        )

    success, msg = await referral_crud.process_instant_referral(
        db=db,
        referrer_code=referral_code,
        new_user_id=current_user.user_id,
        is_email_verified=current_user.is_email_verified
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    return Message(message=msg)


@router.get("/admin/tiers", response_model=List[LoyaltyTierResponse])
async def list_all_tiers(
    db: SessionDep,
    current_user: User = Depends(require_permission("loyalty.manage")),
) -> List[LoyaltyTierResponse]:
    """
    Liệt kê tất cả các hạng thành viên bao gồm cả các hạng đang bị ẩn (Dành cho Admin).
    """
    tiers = await loyalty_tier_crud.get_multi(db=db, limit=100)
    return tiers


@router.post("/admin/tiers", response_model=LoyaltyTierResponse, status_code=status.HTTP_201_CREATED)
async def create_tier(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("loyalty.manage")),
    tier_in: LoyaltyTierCreate,
) -> LoyaltyTierResponse:
    """
    Tạo một hạng thành viên mới với các yêu cầu và quyền lợi xác định (Dành cho Admin).
    """
    tier = await loyalty_tier_crud.create(db=db, obj_in=tier_in)
    await FastAPICache.clear(namespace="loyalty-tiers")
    return tier


@router.patch("/admin/tiers/{tier_id}", response_model=LoyaltyTierResponse)
async def update_tier(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("loyalty.manage")),
    tier_id: int,
    tier_in: LoyaltyTierUpdate,
) -> LoyaltyTierResponse:
    """
    Cập nhật thông tin cấu hình hoặc quyền lợi của một hạng thành viên (Dành cho Admin).
    """
    tier = await loyalty_tier_crud.get(db=db, id=tier_id)
    
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loyalty tier not found"
        )
    
    updated_tier = await loyalty_tier_crud.update(
        db=db,
        db_obj=tier,
        obj_in=tier_in
    )
    
    await FastAPICache.clear(namespace="loyalty-tiers")
    return updated_tier


@router.delete("/admin/tiers/{tier_id}", response_model=Message)
async def delete_tier(
    db: SessionDep,
    tier_id: int,
    current_user: User = Depends(require_permission("loyalty.manage")),
) -> Message:
    """
    Xóa một hạng thành viên (Chỉ được xóa nếu hạng đó không chứa thành viên nào đang hoạt động).
    """
    tier = await loyalty_tier_crud.get(db=db, id=tier_id)
    
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loyalty tier not found"
        )
    
    from sqlalchemy import select, func
    from app.models.loyalty import LoyaltyPoint
    
    stmt = select(func.count(LoyaltyPoint.loyalty_id)).where(
        LoyaltyPoint.tier_id == tier_id
    )
    result = await db.execute(stmt)
    count = result.scalar_one()
    
    if count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete tier with {count} active members"
        )
    
    await loyalty_tier_crud.delete(db=db, id=tier_id)
    await FastAPICache.clear(namespace="loyalty-tiers")
    
    return Message(message="Loyalty tier deleted successfully")


@router.post("/admin/earn", response_model=LoyaltyPointResponse)
async def award_points(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("loyalty.manage")),
    earn_data: EarnPointsRequest,
) -> LoyaltyPointResponse:
    """
    Thực hiện cộng điểm thưởng thủ công cho người dùng (Dành cho Admin).
    """
    loyalty = await loyalty_point_crud.earn_points(
        db=db,
        user_id=earn_data.user_id,
        points=earn_data.points,
        transaction_type=LoyaltyTransactionEnum.ADJUSTMENT,
        description=f"Admin award: {earn_data.description}"
    )
    
    return LoyaltyPointResponse(
        loyalty_id=loyalty.loyalty_id,
        user_id=loyalty.user_id,
        points_balance=loyalty.points_balance,
        total_earned=loyalty.total_earned,
        total_spent=loyalty.total_spent,
        tier_id=loyalty.tier_id,
        created_at=loyalty.created_at,
        updated_at=loyalty.updated_at
    )


@router.post("/admin/referrals/reward", response_model=ReferralResponse)
async def reward_referral_manually(
    *,
    db: SessionDep,
    current_user: User = Depends(require_permission("loyalty.manage")),
    reward_data: ReferralRewardRequest,
) -> ReferralResponse:
    """
    Xác nhận và trao thưởng thủ công cho các yêu cầu giới thiệu người dùng mới (Dành cho Admin).
    """
    referral = await referral_crud.get_by_code(db=db, code=reward_data.referral_code)
    
    if not referral:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referral not found"
        )
    
    rewarded_referral = await referral_crud.reward_referral(
        db=db,
        referral_id=referral.referral_id
    )
    
    return ReferralResponse(
        referral_id=rewarded_referral.referral_id,
        referrer_id=rewarded_referral.referrer_id,
        referred_user_id=rewarded_referral.referred_user_id,
        referral_code=rewarded_referral.referral_code,
        reward_points=rewarded_referral.reward_points,
        is_rewarded=rewarded_referral.is_rewarded,
        rewarded_at=rewarded_referral.rewarded_at,
        created_at=rewarded_referral.created_at
    )


@router.post("/admin/expire-points", response_model=dict)
async def expire_old_points(
    db: SessionDep,
    current_user: User = Depends(require_permission("loyalty.manage")),
) -> dict:
    """
    Thực hiện quét và hủy các điểm thưởng đã hết hạn sử dụng (Dành cho Admin).
    """
    affected = await point_transaction_crud.expire_old_points(db=db)
    
    return {
        "message": f"Expired points for {affected} users",
        "affected_users": affected
    }


@router.get("/admin/stats", response_model=dict)
async def get_loyalty_stats(
    db: SessionDep,
    current_user: User = Depends(require_permission("loyalty.manage")),
) -> dict:
    """
    Lấy các thông số thống kê tổng quát về chương trình khách hàng thân thiết (Dành cho Admin).
    """
    from sqlalchemy import select, func
    from app.models.loyalty import LoyaltyPoint, PointTransaction, Referral
    
    total_users_stmt = select(func.count(LoyaltyPoint.loyalty_id))
    total_users = (await db.execute(total_users_stmt)).scalar_one()
    
    total_points_stmt = select(func.sum(LoyaltyPoint.points_balance))
    total_points = (await db.execute(total_points_stmt)).scalar_one() or 0
    
    total_txn_stmt = select(func.count(PointTransaction.transaction_id))
    total_txn = (await db.execute(total_txn_stmt)).scalar_one()
    
    total_ref_stmt = select(func.count(Referral.referral_id))
    total_ref = (await db.execute(total_ref_stmt)).scalar_one()
    
    rewarded_ref_stmt = select(func.count(Referral.referral_id)).where(
        Referral.is_rewarded == True
    )
    rewarded_ref = (await db.execute(rewarded_ref_stmt)).scalar_one()
    
    return {
        "total_members": total_users,
        "total_points_in_circulation": total_points,
        "total_transactions": total_txn,
        "total_referrals": total_ref,
        "rewarded_referrals": rewarded_ref,
        "pending_referrals": total_ref - rewarded_ref
    }