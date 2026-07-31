from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.system_setting import SystemSetting


class SystemSettingRepositoryInterface(ABC):
    """
    Abstract interface for persisting and retrieving system settings.
    Why: Assures low coupling and high mockability during testing.
    """
    @abstractmethod
    def get(self, key: str) -> Optional[SystemSetting]:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> SystemSetting:
        pass

    @abstractmethod
    def list_all(self) -> List[SystemSetting]:
        pass
