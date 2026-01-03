from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List, Dict

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text, Numeric
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import LoyaltyTransactionEnum

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.order import Order



class LoyaltyTierBase(SQLModel):
    tier_name: str = Field(max_length=50, unique=True, index=True)
    min_points: int = Field(default=0, ge=0)
    discount_percentage: Decimal = Field(
        default=Decimal("0.00"), 
        sa_column=Column(Numeric(5, 2)),
        ge=0,
        le=100
    )
    benefits: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_active: bool = Field(default=True)


class LoyaltyTier(LoyaltyTierBase, table=True):
    __tablename__ = "loyalty_tiers"

    tier_id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    loyalty_points: List["LoyaltyPoint"] = Relationship(back_populates="tier")


class LoyaltyTierResponse(LoyaltyTierBase):
    tier_id: int
    created_at: datetime


class LoyaltyTierCreate(LoyaltyTierBase):
    pass


class LoyaltyTierUpdate(SQLModel):
    tier_name: Optional[str] = Field(default=None, max_length=50)
    min_points: Optional[int] = Field(default=None, ge=0)
    discount_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)
    benefits: Optional[str] = None
    is_active: Optional[bool] = None


class LoyaltyTiersResponse(SQLModel):
    data: List[LoyaltyTierResponse]
    count: int



class LoyaltyPointBase(SQLModel):
    user_id: int = Field(foreign_key="users.user_id", unique=True, index=True)
    points_balance: int = Field(default=0, ge=0)
    total_earned: int = Field(default=0, ge=0)
    total_spent: int = Field(default=0, ge=0)
    tier_id: Optional[int] = Field(default=None, foreign_key="loyalty_tiers.tier_id")


class LoyaltyPoint(LoyaltyPointBase, table=True):
    __tablename__ = "loyalty_points"

    loyalty_id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    user: Optional["User"] = Relationship(back_populates="loyalty_points")
    tier: Optional["LoyaltyTier"] = Relationship(back_populates="loyalty_points")


class LoyaltyPointResponse(LoyaltyPointBase):
    loyalty_id: int
    created_at: datetime
    updated_at: datetime
    tier: Optional[Dict] = None


class LoyaltyPointCreate(LoyaltyPointBase):
    pass


class LoyaltyPointUpdate(SQLModel):
    points_balance: Optional[int] = Field(default=None, ge=0)
    total_earned: Optional[int] = Field(default=None, ge=0)
    total_spent: Optional[int] = Field(default=None, ge=0)
    tier_id: Optional[int] = None



class PointTransactionBase(SQLModel):
    user_id: int = Field(foreign_key="users.user_id")
    transaction_type: LoyaltyTransactionEnum = Field(
        sa_column=Column(PgEnum(LoyaltyTransactionEnum, name="loyalty_transaction_enum", create_type=True), nullable=False)
    )
    points: int
    order_id: Optional[int] = Field(default=None, foreign_key="orders.order_id")
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    expires_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=True)))


class PointTransaction(PointTransactionBase, table=True):
    __tablename__ = "point_transactions"

    transaction_id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    user: Optional["User"] = Relationship(back_populates="point_transactions")
    order: Optional["Order"] = Relationship(back_populates="point_transactions")


class PointTransactionResponse(PointTransactionBase):
    transaction_id: int
    created_at: datetime


class PointTransactionCreate(SQLModel):
    user_id: int
    transaction_type: LoyaltyTransactionEnum
    points: int
    order_id: Optional[int] = None
    description: Optional[str] = None
    expires_at: Optional[datetime] = None


class PointTransactionsResponse(SQLModel):
    data: List[PointTransactionResponse]
    count: int



class ReferralBase(SQLModel):
    referrer_id: int = Field(foreign_key="users.user_id")
    referred_user_id: int = Field(foreign_key="users.user_id")
    referral_code: str = Field(max_length=50, unique=True, index=True)
    reward_points: int = Field(default=0, ge=0)
    is_rewarded: bool = Field(default=False)
    rewarded_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=True)))


class Referral(ReferralBase, table=True):
    __tablename__ = "referrals"

    referral_id: Optional[int] = Field(default=None, primary_key=True)
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    referrer: Optional["User"] = Relationship(
        back_populates="referrals_given",
        sa_relationship_kwargs={"foreign_keys": "[Referral.referrer_id]"}
    )
    referred_user: Optional["User"] = Relationship(
        back_populates="referrals_received",
        sa_relationship_kwargs={"foreign_keys": "[Referral.referred_user_id]"}
    )


class ReferralResponse(ReferralBase):
    referral_id: int
    created_at: datetime
    referrer: Optional[Dict] = None
    referred_user: Optional[Dict] = None


class ReferralCreate(SQLModel):
    referrer_id: int
    referred_user_id: int
    referral_code: str
    reward_points: int = 100


class ReferralUpdate(SQLModel):
    reward_points: Optional[int] = Field(default=None, ge=0)
    is_rewarded: Optional[bool] = None
    rewarded_at: Optional[datetime] = None


class ReferralsResponse(SQLModel):
    data: List[ReferralResponse]
    count: int



class EarnPointsRequest(SQLModel):
    """Request to manually award points"""
    user_id: int
    points: int = Field(gt=0)
    description: str


class RedeemPointsRequest(SQLModel):
    """Request to redeem points"""
    points: int = Field(gt=0)
    description: Optional[str] = "Points redeemed"


class ReferralRewardRequest(SQLModel):
    """Request to reward referral"""
    referral_code: str