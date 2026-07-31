from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.system_setting import SystemSetting
from app.infrastructure.db.repositories.system_setting_repository import SQLAlchemySystemSettingRepository


class SystemSettingService:
    """
    Service layer for managing system settings key-value config records.
    Why: Decouples business logic from direct repository operations.
    """
    def __init__(self, db: Session) -> None:
        self.repo = SQLAlchemySystemSettingRepository(db)

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Lookup setting string value matching target key."""
        setting = self.repo.get(key)
        if not setting:
            return default
        return setting.value

    def get_bool_setting(self, key: str, default: bool = False) -> bool:
        """Lookup setting parsed as boolean."""
        val = self.get_setting(key)
        if val is None:
            return default
        return val.lower() == "true"

    def set_setting(self, key: str, value: str) -> SystemSetting:
        """Upsert stored setting value."""
        return self.repo.set(key, value)

    def list_all(self) -> List[SystemSetting]:
        """List all configurations stored in the database."""
        return self.repo.list_all()
