from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.user import Address, AddressCreate, AddressUpdate

class CRUDAddress(CRUDBase[Address, AddressCreate, AddressUpdate]):
    
    async def get_by_user(
        self, *, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Address]:
        statement = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_default(self, *, db: AsyncSession, user_id: int) -> Optional[Address]:
        statement = select(Address).where(
            Address.user_id == user_id,
            Address.is_default == True
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def set_default(
        self, *, db: AsyncSession, address_id: int, user_id: int
    ) -> Address:
        address = await self.get(db=db, id=address_id)
        if not address or address.user_id != user_id:
            raise ValueError("Address not found")
        
        statement = select(Address).where(
            Address.user_id == user_id,
            Address.is_default == True
        )
        result = await db.execute(statement)
        current_defaults = result.scalars().all()
        
        for addr in current_defaults:
            addr.is_default = False
            db.add(addr)
        
        address.is_default = True
        db.add(address)
        await db.commit()
        await db.refresh(address)
        return address

    async def create_for_user(
        self, *, db: AsyncSession, obj_in: AddressCreate, user_id: int, set_as_default: bool = False
    ) -> Address:
        existing_count = await self.count_by_user(db=db, user_id=user_id)
        is_first = existing_count == 0
        should_be_default = set_as_default or obj_in.is_default or is_first
        
        if should_be_default:
            statement = select(Address).where(Address.user_id == user_id, Address.is_default == True)
            result = await db.execute(statement)
            for addr in result.scalars().all():
                addr.is_default = False
                db.add(addr)

        db_obj = Address(
            user_id=user_id,
            is_default=should_be_default,
            **obj_in.model_dump(exclude={"is_default", "user_id"})
        )
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete_user_address(
        self, *, db: AsyncSession, address_id: int, user_id: int
    ) -> bool:
        statement = select(Address).where(Address.address_id == address_id, Address.user_id == user_id)
        result = await db.execute(statement)
        address = result.scalar_one_or_none()
        
        if not address:
            return False
        
        await db.delete(address)
        await db.commit()
        return True

    async def count_by_user(self, *, db: AsyncSession, user_id: int) -> int:
        from sqlalchemy import func
        statement = select(func.count(Address.address_id)).where(Address.user_id == user_id)
        result = await db.execute(statement)
        return result.scalar_one()

address = CRUDAddress(Address)