"""
Auth models.

Roles and permissions for authorization.
"""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from sqlmodel import Field, Relationship, SQLModel, Column, Text, TIMESTAMP
from sqlalchemy import text

if TYPE_CHECKING:
    from app.models.user import User


# ROLE MODELS

class RoleBase(SQLModel):
    role_name: str = Field(max_length=50, unique=True, index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))


class Role(RoleBase, table=True):
    __tablename__ = "roles"
    
    role_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )
    
    # Relationships
    users: list[User] = Relationship(back_populates="role")
    role_permissions: list[RolePermission] = Relationship(
        back_populates="role",
        cascade_delete=True
    )


class RolePublic(RoleBase):
    role_id: int
    created_at: datetime


class RolePublicWithPermissions(RolePublic):
    permissions: list[PermissionPublic] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(SQLModel):
    role_name: str | None = Field(default=None, max_length=50)
    description: str | None = None


class RolesPublic(SQLModel):
    data: list[RolePublic]
    count: int


# ROLE MODELS

class PermissionBase(SQLModel):
    permission_code: str = Field(max_length=100, unique=True, index=True, description="products:create")
    permission_name: str = Field(max_length=100, description="Tên hiển thị")
    description: str | None = Field(default=None, sa_column=Column(Text))
    resource: str = Field(max_length=50, description="Resource: products, users, orders...")
    action: str = Field(max_length=50, description="Action: read, create, update, delete...")


class Permission(PermissionBase, table=True):
    __tablename__ = "permissions"
    
    permission_id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    )
    
    # Relationships
    role_permissions: list[RolePermission] = Relationship(
        back_populates="permission",
        cascade_delete=True
    )


class PermissionPublic(PermissionBase):
    permission_id: int
    created_at: datetime


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(SQLModel):
    permission_name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    resource: str | None = Field(default=None, max_length=50)
    action: str | None = Field(default=None, max_length=50)


class PermissionsPublic(SQLModel):
    data: list[PermissionPublic]
    count: int


# ROLE-PERMISSION JUNCTION

class RolePermissionBase(SQLModel):
    role_id: int = Field(foreign_key="roles.role_id")
    permission_id: int = Field(foreign_key="permissions.permission_id")


class RolePermission(RolePermissionBase, table=True):
    __tablename__ = "role_permissions"
    
    role_permission_id: int | None = Field(default=None, primary_key=True)
    
    # Relationships
    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")


class RolePermissionCreate(RolePermissionBase):
    pass


class RolePermissionPublic(SQLModel):
    role_permission_id: int
    role_id: int
    permission_id: int


from app.models.user import User 
