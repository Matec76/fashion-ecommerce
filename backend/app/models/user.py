from datetime import datetime, date, timezone, timedelta
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import GenderEnum, AddressTypeEnum

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.cart import Cart
    from app.models.wishlist import Wishlist
    from app.models.loyalty import LoyaltyPoint, PointTransaction, Referral
    from app.models.notification import Notification
    from app.models.review import ProductQuestion
    from app.models.inventory import InventoryTransaction
    from app.models.return_refund import ReturnRequest


class RoleBase(SQLModel):
    role_name: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_active: bool = Field(default=True)


class Role(RoleBase, table=True):
    __tablename__ = "roles"
    role_id: Optional[int] = Field(
        default=None, 
        primary_key=True,
        sa_column_kwargs={"autoincrement": False} 
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    users: List["User"] = Relationship(back_populates="role")
    role_permissions: List["RolePermission"] = Relationship(
        back_populates="role",
        cascade_delete=True
    )


class RoleResponse(RoleBase):
    role_id: int
    created_at: datetime


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    role_name: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RolesResponse(SQLModel):
    data: List[RoleResponse]
    count: int


class PermissionBase(SQLModel):
    permission_code: str = Field(max_length=100, unique=True, index=True)
    permission_name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    resource: Optional[str] = Field(default=None, max_length=50)
    action: Optional[str] = Field(default=None, max_length=50)


class Permission(PermissionBase, table=True):
    __tablename__ = "permissions"

    permission_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    role_permissions: List["RolePermission"] = Relationship(
        back_populates="permission",
        cascade_delete=True
    )


class PermissionResponse(PermissionBase):
    permission_id: int
    created_at: datetime


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(SQLModel):
    permission_code: Optional[str] = Field(default=None, max_length=100)
    permission_name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    resource: Optional[str] = Field(default=None, max_length=50)
    action: Optional[str] = Field(default=None, max_length=50)


class PermissionsResponse(SQLModel):
    data: List[PermissionResponse]
    count: int


class RolePermissionBase(SQLModel):
    role_id: int = Field(foreign_key="roles.role_id")
    permission_id: int = Field(foreign_key="permissions.permission_id")


class RolePermission(RolePermissionBase, table=True):
    __tablename__ = "role_permissions"

    role_permission_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )

    role: Optional["Role"] = Relationship(back_populates="role_permissions")
    permission: Optional["Permission"] = Relationship(back_populates="role_permissions")


class RolePermissionResponse(RolePermissionBase):
    role_permission_id: int
    created_at: datetime


class RolePermissionCreate(RolePermissionBase):
    pass


class UserBase(SQLModel):
    email: str = Field(max_length=255, unique=True, index=True)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = Field(
        default=None,
        sa_column=Column(PgEnum(GenderEnum, name="gender_enum", create_type=True), nullable=True)
    )
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_email_verified: bool = Field(default=False)
    role_id: int = Field(default=2176, foreign_key="roles.role_id")
    referral_code: Optional[str] = Field(default=None, unique=True, index=True, max_length=50)


class User(UserBase, table=True):
    __tablename__ = "users"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255)
    email_verified_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    last_login: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(TIMESTAMP(timezone=True)))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    role: Optional["Role"] = Relationship(back_populates="users")
    addresses: List["Address"] = Relationship(back_populates="user", cascade_delete=True)
    
    orders: List["Order"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Order.user_id]"}
    )

    cancelled_orders: List["Order"] = Relationship(
        back_populates="cancelled_user",
        sa_relationship_kwargs={"primaryjoin": "Order.cancelled_by==User.user_id"}
    )

    carts: List["Cart"] = Relationship(back_populates="user", cascade_delete=True)
    wishlists: List["Wishlist"] = Relationship(back_populates="user", cascade_delete=True)
    
    loyalty_points: Optional["LoyaltyPoint"] = Relationship(back_populates="user")
    point_transactions: List["PointTransaction"] = Relationship(
        back_populates="user",
        cascade_delete=True
    )
    
    referrals_given: List["Referral"] = Relationship(
        back_populates="referrer",
        sa_relationship_kwargs={"foreign_keys": "[Referral.referrer_id]"}
    )
    referrals_received: List["Referral"] = Relationship(
        back_populates="referred_user",
        sa_relationship_kwargs={"foreign_keys": "[Referral.referred_user_id]"}
    )
    
    notifications: List["Notification"] = Relationship(back_populates="user", cascade_delete=True)
    
    product_questions: List["ProductQuestion"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[ProductQuestion.user_id]"}
    )
    answered_questions: List["ProductQuestion"] = Relationship(
        back_populates="answerer",
        sa_relationship_kwargs={"foreign_keys": "[ProductQuestion.answered_by]"}
    )
    inventory_transactions: List["InventoryTransaction"] = Relationship(back_populates="user", cascade_delete=True)
    return_requests: List["ReturnRequest"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[ReturnRequest.user_id]"},
        cascade_delete=True
    )


class UserResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime


class UserDetailResponse(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime
    role: Optional[RoleResponse] = None


class UserCreate(SQLModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    date_of_birth: Optional[date] = None
    phone_number: Optional[str] = Field(default=None, max_length=20)
    role_id: int = Field(default=2176)


class UserRegister(SQLModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: Optional[date] = None


class UserUpdate(SQLModel):
    email: Optional[str] = Field(default=None, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserUpdateMe(SQLModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class UsersResponse(SQLModel):
    data: List[UserResponse]
    count: int


class AddressBase(SQLModel):
    address_type: AddressTypeEnum = Field(
        default=AddressTypeEnum.SHIPPING,
        sa_column=Column(PgEnum(AddressTypeEnum, name="address_type_enum", create_type=True), nullable=False)
    )
    recipient_name: str = Field(max_length=255)
    phone_number: str = Field(max_length=20)
    street_address: str = Field(max_length=255)
    ward: Optional[str] = Field(default=None, max_length=100)
    city: str = Field(max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    is_default: bool = Field(default=False)


class Address(AddressBase, table=True):
    __tablename__ = "addresses"
    address_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=7))),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    user: Optional["User"] = Relationship(back_populates="addresses")


class AddressResponse(AddressBase):
    address_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class AddressCreate(AddressBase):
    pass


class AddressUpdate(SQLModel):
    address_type: Optional[AddressTypeEnum] = None
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    street_address: Optional[str] = Field(default=None, max_length=255)
    ward: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    is_default: Optional[bool] = None


class AddressesResponse(SQLModel):
    data: List[AddressResponse]
    count: int