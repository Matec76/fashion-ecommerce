from typing import Any, Dict, Optional, List
from datetime import datetime, timezone

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User, UserCreate, UserUpdate, UserRegister


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    
    def _apply_search_filter(self, query, search: str):
        search_term = f"%{search.lower()}%"
        return query.where(or_(
            func.lower(User.email).like(search_term),
            func.lower(User.first_name).like(search_term),
            func.lower(User.last_name).like(search_term),
            func.lower(User.phone_number).like(search_term)
        ))

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None,
    ) -> List[User]:
        statement = select(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    statement = statement.where(getattr(self.model, key) == value)

        if search:
            statement = self._apply_search_filter(statement, search)

        if hasattr(self.model, 'created_at'):
            statement = statement.order_by(self.model.created_at.desc())

        statement = statement.offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_multi_with_role(
        self,
        *,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None
    ) -> List[User]:
        statement = select(User).options(selectinload(User.role))

        if filters:
            for key, value in filters.items():
                if hasattr(User, key) and value is not None:
                    statement = statement.where(getattr(User, key) == value)
        
        if search:
            statement = self._apply_search_filter(statement, search)

        statement = statement.offset(skip).limit(limit)
        
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_count(
        self,
        db: AsyncSession,
        *,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None
    ) -> int:
        statement = select(func.count(User.user_id))

        if filters:
            for key, value in filters.items():
                if hasattr(User, key) and value is not None:
                    statement = statement.where(getattr(User, key) == value)
        
        if search:
            statement = self._apply_search_filter(statement, search)

        result = await db.execute(statement)
        return result.scalar_one()

    async def get_by_email(self, *, db: AsyncSession, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(self, *, db: AsyncSession, obj_in: UserCreate, flush: bool = False) -> User:
        db_obj_data = obj_in.model_dump(exclude={"password"})
        db_obj = User(
            **db_obj_data,
            hashed_password=get_password_hash(obj_in.password),
            role_id=obj_in.role_id or 1
        )
        db.add(db_obj)
        if flush:
            await db.flush()
        else:
            await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def register(self, *, db: AsyncSession, obj_in: UserRegister) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            phone_number=getattr(obj_in, 'phone_number', None),
            role_id=1,
            is_active=True,
            is_superuser=False,
            is_email_verified=False,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(self, *, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(db=db, email=email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_password(self, *, db: AsyncSession, user: User, new_password: str) -> User:
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_last_login(self, *, db: AsyncSession, user: User) -> User:
        user.last_login = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def verify_email(self, *, db: AsyncSession, user: User) -> User:
        user.is_email_verified = True
        user.email_verification_token = None
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def is_active(self, user: User) -> bool:
        return user.is_active

    async def is_superuser(self, user: User) -> bool:
        return user.is_superuser


user = CRUDUser(User)
