from typing import Any, Generic, Type, TypeVar, List, Optional, Dict

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.core.db import AsyncSession as DBSession

# TypeVars cho Generic
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base CRUD class với các operations chung.
    
    Generic types:
        - ModelType: SQLModel table class (ví dụ: User, Product)
        - CreateSchemaType: Pydantic model cho create operation
        - UpdateSchemaType: Pydantic model cho update operation
    """

    def __init__(self, model: Type[ModelType]):
        """
        CRUD object với default methods để Create, Read, Update, Delete (CRUD).
        
        Args:
            model: SQLModel table class
        """
        self.model = model

    async def get(
        self,
        *,
        db: AsyncSession,
        id: int,
        raise_404: bool = True
    ) -> Optional[ModelType]:
        """
        Lấy một record theo ID.
        
        Args:
            db: Database session
            id: ID của record
            raise_404: Raise HTTPException 404 nếu không tìm thấy
            
        Returns:
            Model instance hoặc None
            
        Raises:
            HTTPException: 404 nếu không tìm thấy và raise_404=True
        """
        # Lấy primary key column name
        pk_column = list(self.model.__table__.primary_key.columns)[0]
        
        statement = select(self.model).where(pk_column == id)
        result = await db.execute(statement)
        obj = result.scalar_one_or_none()
        
        if not obj and raise_404:
            raise HTTPException(
                status_code=404,
                detail=f"{self.model.__name__} not found"
            )
        
        return obj

    async def get_multi(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Lấy danh sách records với pagination và filters.
        
        Args:
            db: Database session
            skip: Số records bỏ qua (offset)
            limit: Số records tối đa trả về
            filters: Dict filters {column_name: value}
            order_by: Tên column để sort
            order_desc: Sort descending nếu True
            
        Returns:
            List các model instances
        """
        statement = select(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if value is not None:
                        statement = statement.where(column == value)
        
        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                statement = statement.order_by(column.desc())
            else:
                statement = statement.order_by(column)
        
        # Apply pagination
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def count(
        self,
        *,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Đếm số lượng records.
        
        Args:
            db: Database session
            filters: Dict filters {column_name: value}
            
        Returns:
            Số lượng records
        """
        statement = select(func.count()).select_from(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if value is not None:
                        statement = statement.where(column == value)
        
        result = await db.execute(statement)
        return result.scalar_one()

    async def create(
        self,
        *,
        db: AsyncSession,
        obj_in: CreateSchemaType,
        flush: bool = False
    ) -> ModelType:
        """
        Tạo record mới.
        
        Args:
            db: Database session
            obj_in: Pydantic model chứa data để create
            flush: Chỉ flush thay vì commit (dùng trong transaction)
            
        Returns:
            Model instance đã tạo
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        
        db.add(db_obj)
        
        if flush:
            await db.flush()
        else:
            await db.commit()
            
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        *,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any],
        flush: bool = False
    ) -> ModelType:
        """
        Cập nhật record.
        
        Args:
            db: Database session
            db_obj: Model instance hiện tại
            obj_in: Pydantic model hoặc dict chứa data để update
            flush: Chỉ flush thay vì commit
            
        Returns:
            Model instance đã cập nhật
        """
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        
        if flush:
            await db.flush()
        else:
            await db.commit()
            
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        *,
        db: AsyncSession,
        id: int,
        soft_delete: bool = False
    ) -> ModelType:
        """
        Xóa record.
        
        Args:
            db: Database session
            id: ID của record cần xóa
            soft_delete: Soft delete (set deleted_at) nếu True
            
        Returns:
            Model instance đã xóa
            
        Raises:
            HTTPException: 404 nếu không tìm thấy
        """
        obj = await self.get(db=db, id=id)
        
        if soft_delete and hasattr(obj, 'deleted_at'):
            # Soft delete
            from datetime import datetime
            obj.deleted_at = datetime.utcnow()
            await db.commit()
            await db.refresh(obj)
        else:
            # Hard delete
            await db.delete(obj)
            await db.commit()
        
        return obj

    async def restore(
        self,
        *,
        db: AsyncSession,
        id: int
    ) -> Optional[ModelType]:
        """
        Khôi phục record đã soft delete.
        
        Args:
            db: Database session
            id: ID của record cần khôi phục
            
        Returns:
            Model instance đã khôi phục hoặc None
        """
        if not hasattr(self.model, 'deleted_at'):
            return None
        
        obj = await self.get(db=db, id=id, raise_404=False)
        
        if obj and obj.deleted_at:
            obj.deleted_at = None
            await db.commit()
            await db.refresh(obj)
            return obj
        
        return None

    async def search(
        self,
        *,
        db: AsyncSession,
        query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Tìm kiếm records theo text.
        
        Args:
            db: Database session
            query: Text để tìm kiếm
            search_fields: List tên columns để search
            skip: Offset
            limit: Limit
            
        Returns:
            List các model instances matching
        """
        statement = select(self.model)
        
        # Build OR conditions cho mỗi search field
        conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                conditions.append(column.ilike(f"%{query}%"))
        
        if conditions:
            statement = statement.where(or_(*conditions))
        
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def exists(
        self,
        *,
        db: AsyncSession,
        filters: Dict[str, Any]
    ) -> bool:
        """
        Kiểm tra xem record có tồn tại hay không.
        
        Args:
            db: Database session
            filters: Dict filters {column_name: value}
            
        Returns:
            True nếu tồn tại, False nếu không
        """
        count = await self.count(db=db, filters=filters)
        return count > 0
