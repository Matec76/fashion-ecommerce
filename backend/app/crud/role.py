"""
CRUD operations cho Role và Permission models.

Bao gồm:
- CRUDRole: CRUD cho Role với các phương thức quản lý permissions
- CRUDPermission: CRUD cho Permission
- CRUDRolePermission: CRUD cho RolePermission (many-to-many)
"""
from typing import List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.user import (
    Role,
    RoleCreate,
    RoleUpdate,
    Permission,
    PermissionCreate,
    PermissionUpdate,
    RolePermission,
    RolePermissionCreate,
)


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """CRUD operations cho Role"""

    async def get_by_name(
        self,
        *,
        db: AsyncSession,
        name: str
    ) -> Optional[Role]:
        """
        Lấy role theo tên.
        
        Args:
            db: Database session
            name: Tên role
            
        Returns:
            Role instance hoặc None
        """
        statement = select(Role).where(Role.role_name == name)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_with_permissions(
        self,
        *,
        db: AsyncSession,
        id: int
    ) -> Optional[Role]:
        """
        Lấy role kèm danh sách permissions.
        
        Args:
            db: Database session
            id: Role ID
            
        Returns:
            Role instance với eager loaded permissions
        """
        statement = (
            select(Role)
            .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
            .where(Role.role_id == id)
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def add_permission(
        self,
        *,
        db: AsyncSession,
        role_id: int,
        permission_id: int
    ) -> RolePermission:
        """
        Thêm permission cho role.
        
        Args:
            db: Database session
            role_id: Role ID
            permission_id: Permission ID
            
        Returns:
            RolePermission instance
        """
        # Kiểm tra đã tồn tại chưa
        statement = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
        result = await db.execute(statement)
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Tạo mới
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=permission_id
        )
        db.add(role_permission)
        await db.commit()
        await db.refresh(role_permission)
        return role_permission

    async def remove_permission(
        self,
        *,
        db: AsyncSession,
        role_id: int,
        permission_id: int
    ) -> bool:
        """
        Xóa permission khỏi role.
        
        Args:
            db: Database session
            role_id: Role ID
            permission_id: Permission ID
            
        Returns:
            True nếu xóa thành công, False nếu không tìm thấy
        """
        statement = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
        result = await db.execute(statement)
        role_permission = result.scalar_one_or_none()
        
        if not role_permission:
            return False
        
        await db.delete(role_permission)
        await db.commit()
        return True

    async def get_permissions(
        self,
        *,
        db: AsyncSession,
        role_id: int
    ) -> List[Permission]:
        """
        Lấy danh sách permissions của role.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            List Permission instances
        """
        statement = (
            select(Permission)
            .join(RolePermission)
            .where(RolePermission.role_id == role_id)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def sync_permissions(
        self,
        *,
        db: AsyncSession,
        role_id: int,
        permission_ids: List[int]
    ) -> Role:
        """
        Đồng bộ permissions cho role (xóa cũ, thêm mới).
        
        Args:
            db: Database session
            role_id: Role ID
            permission_ids: List Permission IDs mới
            
        Returns:
            Role instance
        """
        # Xóa tất cả permissions hiện tại
        statement = select(RolePermission).where(RolePermission.role_id == role_id)
        result = await db.execute(statement)
        existing = result.scalars().all()
        
        for rp in existing:
            await db.delete(rp)
        
        # Thêm permissions mới
        for permission_id in permission_ids:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id
            )
            db.add(role_permission)
        
        await db.commit()
        
        # Trả về role với permissions mới
        return await self.get_with_permissions(db=db, id=role_id)


class CRUDPermission(CRUDBase[Permission, PermissionCreate, PermissionUpdate]):
    """CRUD operations cho Permission"""

    async def get_by_code(
        self,
        *,
        db: AsyncSession,
        code: str
    ) -> Optional[Permission]:
        """
        Lấy permission theo code.
        
        Args:
            db: Database session
            code: Permission code
            
        Returns:
            Permission instance hoặc None
        """
        statement = select(Permission).where(Permission.permission_code == code)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_resource_and_action(
        self,
        *,
        db: AsyncSession,
        resource: str,
        action: str
    ) -> Optional[Permission]:
        """
        Lấy permission theo resource và action.
        
        Args:
            db: Database session
            resource: Resource name
            action: Action name
            
        Returns:
            Permission instance hoặc None
        """
        statement = select(Permission).where(
            Permission.resource == resource,
            Permission.action == action
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_resource(
        self,
        *,
        db: AsyncSession,
        resource: str
    ) -> List[Permission]:
        """
        Lấy tất cả permissions của một resource.
        
        Args:
            db: Database session
            resource: Resource name
            
        Returns:
            List Permission instances
        """
        statement = select(Permission).where(Permission.resource == resource)
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_all_grouped(
        self,
        *,
        db: AsyncSession
    ) -> Dict[str, List[Permission]]:
        """
        Lấy tất cả permissions grouped by resource.
        
        Args:
            db: Database session
            
        Returns:
            Dict {resource: [permissions]}
        """
        statement = select(Permission).order_by(Permission.resource, Permission.action)
        result = await db.execute(statement)
        permissions = result.scalars().all()
        
        grouped = {}
        for perm in permissions:
            if perm.resource not in grouped:
                grouped[perm.resource] = []
            grouped[perm.resource].append(perm)
        
        return grouped


class CRUDRolePermission(CRUDBase[RolePermission, RolePermissionCreate, Dict[str, Any]]):
    """CRUD operations cho RolePermission (bảng many-to-many)"""

    async def get_by_role_and_permission(
        self,
        *,
        db: AsyncSession,
        role_id: int,
        permission_id: int
    ) -> Optional[RolePermission]:
        """
        Lấy RolePermission theo role_id và permission_id.
        
        Args:
            db: Database session
            role_id: Role ID
            permission_id: Permission ID
            
        Returns:
            RolePermission instance hoặc None
        """
        statement = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_role(
        self,
        *,
        db: AsyncSession,
        role_id: int
    ) -> List[RolePermission]:
        """
        Lấy tất cả RolePermissions của một role.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            List RolePermission instances
        """
        statement = select(RolePermission).where(RolePermission.role_id == role_id)
        result = await db.execute(statement)
        return result.scalars().all()


# Singleton instances
role = CRUDRole(Role)
permission = CRUDPermission(Permission)
role_permission = CRUDRolePermission(RolePermission)