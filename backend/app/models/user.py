from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from app.models.enums import GenderEnum, AddressTypeEnum

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.cart import Cart
    from app.models.review import Review
    from app.models.wishlist import Wishlist
    from app.models.loyalty import LoyaltyPoint, PointTransaction, Referral
    from app.models.notification import Notification
    from app.models.analytics import ProductView, SearchHistory, UserActivity
    from app.models.review import ProductQuestion
    from app.models.system import AdminActivityLog
    from app.models.inventory import InventoryTransaction
    from app.models.return_refund import ReturnRequest


class RoleBase(SQLModel):
    role_name: str = Field(max_length=50, unique=True, index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    is_active: bool = Field(default=True)


class Role(RoleBase, table=True):
    __tablename__ = "roles"

    role_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )

    users: List["User"] = Relationship(back_populates="role")
    role_permissions: List["RolePermission"] = Relationship(
        back_populates="role",
        cascade_delete=True
    )


class RolePublic(RoleBase):
    role_id: int
    created_at: datetime


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    role_name: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RolesPublic(SQLModel):
    data: List[RolePublic]
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
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )

    role_permissions: List["RolePermission"] = Relationship(
        back_populates="permission",
        cascade_delete=True
    )


class PermissionPublic(PermissionBase):
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


class PermissionsPublic(SQLModel):
    data: List[PermissionPublic]
    count: int


class RolePermissionBase(SQLModel):
    role_id: int = Field(foreign_key="roles.role_id")
    permission_id: int = Field(foreign_key="permissions.permission_id")


class RolePermission(RolePermissionBase, table=True):
    __tablename__ = "role_permissions"

    role_permission_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )

    role: Optional["Role"] = Relationship(back_populates="role_permissions")
    permission: Optional["Permission"] = Relationship(back_populates="role_permissions")


class RolePermissionPublic(RolePermissionBase):
    role_permission_id: int
    created_at: datetime


class RolePermissionCreate(RolePermissionBase):
    pass


class UserBase(SQLModel):
    email: str = Field(max_length=255, unique=True, index=True)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[datetime] = None
    gender: Optional[GenderEnum] = Field(
        default=None,
        sa_column=Column(PgEnum(GenderEnum, name="gender_enum", create_type=False), nullable=True)
    )
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_email_verified: bool = Field(default=False)
    role_id: int = Field(default=3, foreign_key="roles.role_id")


class User(UserBase, table=True):
    __tablename__ = "users"

    user_id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255)
    email_verified_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    role: Optional["Role"] = Relationship(back_populates="users")
    addresses: List["Address"] = Relationship(back_populates="user", cascade_delete=True)
    orders: List["Order"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[Order.user_id]"}
    )
    carts: List["Cart"] = Relationship(back_populates="user", cascade_delete=True)
    reviews: List["Review"] = Relationship(back_populates="user", cascade_delete=True)
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
        back_populates="referee",
        sa_relationship_kwargs={"foreign_keys": "[Referral.referee_id]"}
    )
    notifications: List["Notification"] = Relationship(back_populates="user", cascade_delete=True)
    product_views: List["ProductView"] = Relationship(back_populates="user", cascade_delete=True)
    search_history: List["SearchHistory"] = Relationship(back_populates="user", cascade_delete=True)
    user_activities: List["UserActivity"] = Relationship(back_populates="user", cascade_delete=True)
    product_questions: List["ProductQuestion"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[ProductQuestion.user_id]"}
    )
    answered_questions: List["ProductQuestion"] = Relationship(
        back_populates="answerer",
        sa_relationship_kwargs={"foreign_keys": "[ProductQuestion.answered_by]"}
    )
    admin_logs: List["AdminActivityLog"] = Relationship(back_populates="user", cascade_delete=True)
    inventory_transactions: List["InventoryTransaction"] = Relationship(back_populates="user", cascade_delete=True)
    return_requests: List["ReturnRequest"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[ReturnRequest.user_id]"},
        cascade_delete=True
    )


class UserPublic(UserBase):
    user_id: int
    created_at: datetime
    updated_at: datetime


class UserCreate(SQLModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    role_id: int = Field(default=3)


class UserRegister(SQLModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)


class UserUpdate(SQLModel):
    email: Optional[str] = Field(default=None, max_length=255)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[datetime] = None
    gender: Optional[GenderEnum] = None
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class UserUpdateMe(SQLModel):
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[datetime] = None
    gender: Optional[GenderEnum] = None


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class UsersPublic(SQLModel):
    data: List[UserPublic]
    count: int


class AddressBase(SQLModel):
    user_id: int = Field(foreign_key="users.user_id")
    address_type: AddressTypeEnum = Field(
        default=AddressTypeEnum.SHIPPING,
        sa_column=Column(PgEnum(AddressTypeEnum, name="address_type_enum", create_type=False), nullable=False)
    )
    recipient_name: str = Field(max_length=255)
    phone_number: str = Field(max_length=20)
    address_line1: str = Field(max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(max_length=100)
    state_province: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    country: str = Field(default="Vietnam", max_length=100)
    is_default: bool = Field(default=False)


class Address(AddressBase, table=True):
    __tablename__ = "addresses"

    address_id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    )

    user: Optional["User"] = Relationship(back_populates="addresses")


class AddressPublic(AddressBase):
    address_id: int
    created_at: datetime
    updated_at: datetime


class AddressCreate(AddressBase):
    pass


class AddressUpdate(SQLModel):
    address_type: Optional[AddressTypeEnum] = None
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    address_line1: Optional[str] = Field(default=None, max_length=255)
    address_line2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state_province: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)
    is_default: Optional[bool] = None


class AddressesPublic(SQLModel):
    data: List[AddressPublic]
    count: int
