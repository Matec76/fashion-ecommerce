from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.system import (
    SystemSetting,
    SystemSettingCreate,
    SystemSettingUpdate,
)
from app.models.enums import SettingTypeEnum

class CRUDSystemSetting(CRUDBase[SystemSetting, SystemSettingCreate, SystemSettingUpdate]):
    async def get_by_key(
        self,
        *,
        db: AsyncSession,
        key: str
    ) -> Optional[SystemSetting]:
        statement = select(SystemSetting).where(SystemSetting.setting_key == key)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_value(
        self,
        *,
        db: AsyncSession,
        key: str,
        default: Any = None
    ) -> Any:
        setting = await self.get_by_key(db=db, key=key)
        
        if not setting:
            return default
        
        if setting.setting_type == SettingTypeEnum.STRING:
            return setting.setting_value
        elif setting.setting_type == SettingTypeEnum.NUMBER:
            try:
                return float(setting.setting_value) if '.' in setting.setting_value else int(setting.setting_value)
            except (ValueError, TypeError, AttributeError):
                return default
        elif setting.setting_type == SettingTypeEnum.BOOLEAN:
            if isinstance(setting.setting_value, bool):
                return setting.setting_value
            return str(setting.setting_value).lower() in ['true', '1', 'yes', 'on']
        elif setting.setting_type == SettingTypeEnum.JSON:
            try:
                import json
                return json.loads(setting.setting_value) if isinstance(setting.setting_value, str) else setting.setting_value
            except (ValueError, TypeError):
                return default
        else:
            return setting.setting_value

    async def set_value(
        self,
        *,
        db: AsyncSession,
        key: str,
        value: Any,
        type: SettingTypeEnum = SettingTypeEnum.STRING,
        description: Optional[str] = None,
        is_public: bool = False,
        updated_by: Optional[int] = None
    ) -> SystemSetting:
        if type == SettingTypeEnum.JSON and not isinstance(value, (dict, list)):
             import json
             try:
                 value = json.loads(value)
             except:
                 pass
        
        setting = await self.get_by_key(db=db, key=key)
        
        if setting:
            setting.setting_value = value
            setting.setting_type = type
            if description:
                setting.description = description
            setting.is_public = is_public
            setting.updated_by = updated_by
            
            db.add(setting)
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=value,
                setting_type=type,
                description=description,
                is_public=is_public,
                updated_by=updated_by
            )
            db.add(setting)
            
        await db.commit()
        await db.refresh(setting)
        return setting

    async def get_public_settings(
        self,
        *,
        db: AsyncSession
    ) -> List[SystemSetting]:
        statement = (
            select(SystemSetting)
            .where(SystemSetting.is_public == True)
            .order_by(SystemSetting.setting_key)
        )
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_all_as_dict(
        self,
        *,
        db: AsyncSession,
        public_only: bool = False
    ) -> Dict[str, Any]:
        if public_only:
            settings = await self.get_public_settings(db=db)
        else:
            settings = await self.get_multi(db=db, limit=1000)
        
        result = {}
        for setting in settings:
            val = setting.setting_value
            if setting.setting_type == SettingTypeEnum.BOOLEAN:
                 if isinstance(val, str):
                    val = val.lower() in ['true', '1', 'yes', 'on']
            elif setting.setting_type == SettingTypeEnum.NUMBER:
                try:
                    val = float(val) if '.' in str(val) else int(val)
                except:
                    pass
            
            result[setting.setting_key] = val
        
        return result

system_setting = CRUDSystemSetting(SystemSetting)