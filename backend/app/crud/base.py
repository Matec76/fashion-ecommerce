from typing import Any, Generic, Type, TypeVar, List, Optional, Dict, Tuple
from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, or_, inspect, update as sql_update, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):

    def __init__(self, model: Type[ModelType]):
        self.model = model
        self._pk_column = None

    def _get_primary_key_column(self) -> InstrumentedAttribute:
        if self._pk_column is not None:
            return self._pk_column
        
        mapper = inspect(self.model)
        pk_columns = [col for col in mapper.columns if col.primary_key]
        
        if not pk_columns:
            raise ValueError(f"Model {self.model.__name__} has no primary key")
        
        if len(pk_columns) > 1:
            raise ValueError(
                f"Model {self.model.__name__} has composite primary key. "
                "Override _get_primary_key_column() to handle this case."
            )
        
        pk_name = pk_columns[0].name
        self._pk_column = getattr(self.model, pk_name)
        
        return self._pk_column

    def _get_primary_key_value(self, obj: ModelType) -> Any:
        pk_column = self._get_primary_key_column()
        return getattr(obj, pk_column.key)

    async def get(
        self,
        *,
        db: AsyncSession,
        id: Any,
        raise_404: bool = True
    ) -> Optional[ModelType]:
        pk_column = self._get_primary_key_column()
        
        statement = select(self.model).where(pk_column == id)
        result = await db.execute(statement)
        obj = result.scalar_one_or_none()
        
        if not obj and raise_404:
            raise HTTPException(
                status_code=404,
                detail=f"{self.model.__name__} with id {id} not found"
            )
        
        return obj

    async def get_by(
        self,
        *,
        db: AsyncSession,
        raise_404: bool = False,
        **filters
    ) -> Optional[ModelType]:
        statement = select(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                column = getattr(self.model, key)
                statement = statement.where(column == value)
        
        result = await db.execute(statement)
        obj = result.scalar_one_or_none()
        
        if not obj and raise_404:
            filter_str = ", ".join([f"{k}={v}" for k, v in filters.items()])
            raise HTTPException(
                status_code=404,
                detail=f"{self.model.__name__} with {filter_str} not found"
            )
        
        return obj

    async def exists(
        self,
        *,
        db: AsyncSession,
        **filters
    ) -> bool:
        statement = select(func.count()).select_from(self.model)
        
        for key, value in filters.items():
            if hasattr(self.model, key):
                column = getattr(self.model, key)
                statement = statement.where(column == value)
        
        result = await db.execute(statement)
        count = result.scalar_one()
        return count > 0

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
        statement = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if value is not None:
                        if isinstance(value, (list, tuple)):
                            statement = statement.where(column.in_(value))
                        else:
                            statement = statement.where(column == value)
        
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                statement = statement.order_by(column.desc())
            else:
                statement = statement.order_by(column)
        
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_all(
        self,
        *,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        statement = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if value is not None:
                        statement = statement.where(column == value)
        
        if order_by and hasattr(self.model, order_by):
            column = getattr(self.model, order_by)
            if order_desc:
                statement = statement.order_by(column.desc())
            else:
                statement = statement.order_by(column)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        statement = select(func.count()).select_from(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if value is not None:
                        if isinstance(value, (list, tuple)):
                            statement = statement.where(column.in_(value))
                        else:
                            statement = statement.where(column == value)
        
        result = await db.execute(statement)
        return result.scalar_one()

    async def create(
        self,
        *,
        db: AsyncSession,
        obj_in: CreateSchemaType | Dict[str, Any],
        flush: bool = False,
        refresh: bool = True
    ) -> ModelType:
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump()
        
        db_obj = self.model(**obj_in_data)
        
        db.add(db_obj)
        
        if flush:
            await db.flush()
        else:
            await db.commit()
        
        if refresh:
            await db.refresh(db_obj)
        
        return db_obj

    async def get_or_create(
        self,
        *,
        db: AsyncSession,
        defaults: Optional[Dict[str, Any]] = None,
        **filters
    ) -> Tuple[ModelType, bool]:
        obj = await self.get_by(db=db, **filters)
        
        if obj:
            return obj, False
        
        create_data = {**filters}
        if defaults:
            create_data.update(defaults)
        
        obj = await self.create(db=db, obj_in=create_data)
        return obj, True

    async def bulk_create(
        self,
        *,
        db: AsyncSession,
        objs_in: List[CreateSchemaType | Dict[str, Any]],
        flush: bool = False
    ) -> List[ModelType]:
        db_objs = []
        
        for obj_in in objs_in:
            if isinstance(obj_in, dict):
                obj_in_data = obj_in
            else:
                obj_in_data = obj_in.model_dump()
            
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        
        if flush:
            await db.flush()
        else:
            await db.commit()
        
        for db_obj in db_objs:
            await db.refresh(db_obj)
        
        return db_objs

    async def update(
        self,
        *,
        db: AsyncSession,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any],
        flush: bool = False,
        refresh: bool = True
    ) -> ModelType:
        obj_data = db_obj.model_dump()
        
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
        
        if refresh:
            await db.refresh(db_obj)
        
        return db_obj

    async def bulk_update(
        self,
        *,
        db: AsyncSession,
        objs: List[ModelType],
        flush: bool = False
    ) -> List[ModelType]:
        db.add_all(objs)
        
        if flush:
            await db.flush()
        else:
            await db.commit()
        
        for obj in objs:
            await db.refresh(obj)
        
        return objs

    async def update_by_id(
        self,
        *,
        db: AsyncSession,
        id: Any,
        obj_in: UpdateSchemaType | Dict[str, Any],
        flush: bool = False
    ) -> ModelType:
        db_obj = await self.get(db=db, id=id)
        return await self.update(db=db, db_obj=db_obj, obj_in=obj_in, flush=flush)

    async def delete(
        self,
        *,
        db: AsyncSession,
        id: Any,
        soft_delete: bool = False
    ) -> ModelType:
        obj = await self.get(db=db, id=id)
        
        if soft_delete and hasattr(obj, 'deleted_at'):
            obj.deleted_at = datetime.now(timezone(timedelta(hours=7)))
            await db.commit()
            await db.refresh(obj)
        else:
            await db.delete(obj)
            await db.commit()
        
        return obj

    async def delete_by(
        self,
        *,
        db: AsyncSession,
        soft_delete: bool = False,
        **filters
    ) -> Optional[ModelType]:
        obj = await self.get_by(db=db, **filters)
        
        if not obj:
            return None
        
        pk_value = self._get_primary_key_value(obj)
        return await self.delete(db=db, id=pk_value, soft_delete=soft_delete)

    async def bulk_delete(
        self,
        *,
        db: AsyncSession,
        ids: List[Any],
        soft_delete: bool = False
    ) -> int:
        pk_column = self._get_primary_key_column()
        
        if soft_delete and hasattr(self.model, 'deleted_at'):
            statement = (
                sql_update(self.model)
                .where(pk_column.in_(ids))
                .values(deleted_at=datetime.now(timezone(timedelta(hours=7))))
            )
        else:
            statement = sql_delete(self.model).where(pk_column.in_(ids))
        
        result = await db.execute(statement)
        await db.commit()
        
        return result.rowcount

    async def restore(
        self,
        *,
        db: AsyncSession,
        id: Any
    ) -> Optional[ModelType]:
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
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        statement = select(self.model)
        
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                search_conditions.append(column.ilike(f"%{query}%"))
        
        if search_conditions:
            statement = statement.where(or_(*search_conditions))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if value is not None:
                        statement = statement.where(column == value)
        
        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def search_count(
        self,
        *,
        db: AsyncSession,
        query: str,
        search_fields: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        statement = select(func.count()).select_from(self.model)
        
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                search_conditions.append(column.ilike(f"%{query}%"))
        
        if search_conditions:
            statement = statement.where(or_(*search_conditions))
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    column = getattr(self.model, key)
                    if value is not None:
                        statement = statement.where(column == value)
        
        result = await db.execute(statement)
        return result.scalar_one()

    async def get_by_ids(
        self,
        *,
        db: AsyncSession,
        ids: List[Any]
    ) -> List[ModelType]:
        pk_column = self._get_primary_key_column()
        
        statement = select(self.model).where(pk_column.in_(ids))
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_first(
        self,
        *,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> Optional[ModelType]:
        results = await self.get_multi(
            db=db,
            skip=0,
            limit=1,
            filters=filters,
            order_by=order_by,
            order_desc=order_desc
        )
        return results[0] if results else None