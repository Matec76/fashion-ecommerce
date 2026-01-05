from typing import Any, Dict, Optional, List
from datetime import datetime, timezone, timedelta
import secrets
import string

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User, UserCreate, UserUpdate, UserRegister


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    
    def generate_referral_code(self, length: int = 8) -> str:
        """Sinh mã giới thiệu ngẫu nhiên."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))

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

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        statement = select(User).options(selectinload(User.role)).where(User.email == email)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def get_by_referral_code(self, db: AsyncSession, code: str) -> Optional[User]:
        statement = select(User).where(User.referral_code == code)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    

    async def get(self, db: AsyncSession, id: Any) -> Optional[User]:
        statement = select(User).options(selectinload(User.role)).where(User.user_id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def create(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: UserCreate, 
        is_superuser: bool = False
    ) -> User:
        """
        Tạo user mới (Dùng cho Admin tạo user).
        """
        create_data = obj_in.model_dump()
        create_data.pop("password")
        create_data["hashed_password"] = get_password_hash(obj_in.password)
        create_data["is_superuser"] = is_superuser
        code = self.generate_referral_code()
        while True:
            existing = await self.get_by_referral_code(db, code=code)
            if not existing:
                break
            code = self.generate_referral_code()
            
        create_data["referral_code"] = code
        
        db_obj = User(**create_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def register(self, *, db: AsyncSession, obj_in: UserRegister) -> User:
        """
        Đăng ký user mới (Public).
        Tự động sinh referral code.
        """
        code = self.generate_referral_code()
        while True:
            existing = await self.get_by_referral_code(db, code=code)
            if not existing:
                break
            code = self.generate_referral_code()

        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            date_of_birth=getattr(obj_in, "date_of_birth", None),
            role_id=2176,
            is_active=True,
            is_superuser=False,
            is_email_verified=False,
            referral_code=code
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        user = await self.get_by_email(db=db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def update_password(self, *, db: AsyncSession, user: User, new_password: str) -> User:
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_last_login(self, *, db: AsyncSession, user: User) -> User:
        user.last_login = datetime.now(timezone(timedelta(hours=7)))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def verify_email(self, *, db: AsyncSession, user: User) -> User:
        user.is_email_verified = True
        user.email_verified_at = datetime.now(timezone(timedelta(hours=7)))
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def is_active(self, user: User) -> bool:
        return user.is_active

    async def is_superuser(self, user: User) -> bool:
        return user.is_superuser

user = CRUDUser(User)