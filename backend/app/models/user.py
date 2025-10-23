from datetime import datetime, date
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel, Column, TIMESTAMP, Text
from sqlalchemy import text

from app.models.enums import GenderEnum, AddressTypeEnum


# User

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    gender: GenderEnum | None = None
    is_active: bool = True
    is_superuser: bool = False
    is_email_verified: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)
    role_id: int | None = None


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)


class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    gender: GenderEnum | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    is_email_verified: bool | None = None
    role_id: int | None = None


class UserUpdateMe(SQLModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    gender: GenderEnum | None = None


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class User(UserBase, table=True):
    __tablename__ = "users"
    
    user_id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255)
    role_id: int | None = Field(default=1, foreign_key="roles.role_id")
    loyalty_points: int = Field(default=0)
    email_verification_token: str | None = Field(default=None, max_length=255)
    password_reset_token: str | None = Field(default=None, max_length=255)
    password_reset_expires: datetime | None = None
    last_login: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"))
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"), onupdate=text("NOW()"))
    )
    
    # Relationships
    role: "Role" | None = Relationship(back_populates="users")
    addresses: list["Address"] = Relationship(back_populates="user", cascade_delete=True)
    orders: list["Order"] = Relationship(back_populates="user")
    reviews: list["Review"] = Relationship(back_populates="user")
    wishlist: list["Wishlist"] = Relationship(back_populates="user", cascade_delete=True)
    cart: list["Cart"] = Relationship(back_populates="user", cascade_delete=True)
    notifications: list["Notification"] = Relationship(back_populates="user", cascade_delete=True)
    loyalty_transactions: list["LoyaltyTransaction"] = Relationship(back_populates="user")
    product_questions: list["ProductQuestion"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[ProductQuestion.user_id]"}
    )
    answered_questions: list["ProductQuestion"] = Relationship(
        back_populates="answerer",
        sa_relationship_kwargs={"foreign_keys": "[ProductQuestion.answered_by]"}
    )
    admin_logs: list["AdminActivityLog"] = Relationship(back_populates="user")
    return_requests: list["ReturnRequest"] = Relationship(back_populates="user")


class UserPublic(UserBase):
    user_id: int
    role_id: int | None
    loyalty_points: int
    created_at: datetime


class UserPublicWithRole(UserPublic):
    role: "RolePublic" | None = None


class UserMe(UserPublic):
    last_login: datetime | None
    is_email_verified: bool


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Address

class AddressBase(SQLModel):
    address_type: AddressTypeEnum = AddressTypeEnum.SHIPPING
    street_address: str = Field(max_length=255)
    ward: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    city: str = Field(max_length=100)
    country: str = Field(default="Vietnam", max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(SQLModel):
    address_type: AddressTypeEnum | None = None
    street_address: str | None = Field(default=None, max_length=255)
    ward: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    is_default: bool | None = None


class Address(AddressBase, table=True):
    __tablename__ = "addresses"
    
    address_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user_id")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("NOW()"))
    )
    
    # Relationships
    user: User = Relationship(back_populates="addresses")


class AddressPublic(AddressBase):
    address_id: int
    user_id: int
    created_at: datetime


class AddressesPublic(SQLModel):
    data: list[AddressPublic]
    count: int


# Forward references để tránh circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.auth import Role, RolePublic
    from app.models.order import Order
    from app.models.review import Review, ProductQuestion
    from app.models.wishlist import Wishlist
    from app.models.cart import Cart
    from app.models.notification import Notification
    from app.models.loyalty import LoyaltyTransaction
    from app.models.system import AdminActivityLog
    from app.models.return_refund import ReturnRequest
