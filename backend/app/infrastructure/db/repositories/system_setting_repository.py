from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.domain.entities.system_setting import SystemSetting
from app.domain.interfaces.system_setting_repository import SystemSettingRepositoryInterface
from app.infrastructure.db.models.system_setting_model import SystemSettingModel


class SQLAlchemySystemSettingRepository(SystemSettingRepositoryInterface):
    """
    SQLAlchemy-based concrete implementation of SystemSettingRepositoryInterface.
    Why: Handles mapping and DB CRUD transactions for system settings.
    """
    def __init__(self, db: Session) -> None:
        self.db = db

    def _to_domain(self, model: SystemSettingModel) -> SystemSetting:
        """Helper to map SQLAlchemy DB model to pure domain SystemSetting entity."""
        return SystemSetting(
            key=model.key,
            value=model.value,
            updated_at=model.updated_at
        )

    def get(self, key: str) -> Optional[SystemSetting]:
        """Lookup stored setting matching target key."""
        model = self.db.query(SystemSettingModel).filter(SystemSettingModel.key == key).first()
        if not model:
            return None
        return self._to_domain(model)

    def set(self, key: str, value: str) -> SystemSetting:
        """Upsert a system setting key-value pair."""
        model = self.db.query(SystemSettingModel).filter(SystemSettingModel.key == key).first()
        if model:
            model.value = value
            model.updated_at = datetime.now(timezone.utc)
        else:
            model = SystemSettingModel(
                key=key,
                value=value,
                updated_at=datetime.now(timezone.utc)
            )
            self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def list_all(self) -> List[SystemSetting]:
        """List all stored configurations."""
        models = self.db.query(SystemSettingModel).all()
        return [self._to_domain(m) for m in models]
