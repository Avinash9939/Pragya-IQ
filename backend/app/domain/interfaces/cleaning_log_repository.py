from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.cleaning_log import CleaningLog

class CleaningLogRepositoryInterface(ABC):
    """
    Abstract repository interface managing CleaningLog data lookup and persistence.
    Why: Enforces Dependency Inversion so service layers are decoupled from DB models.
    """

    @abstractmethod
    def create(self, log: CleaningLog) -> CleaningLog:
        """Create a new cleaning log audit record."""
        pass

    @abstractmethod
    def get_by_dataset_id(self, dataset_id: int) -> List[CleaningLog]:
        """Lookup all cleaning log events recorded for a specific dataset."""
        pass
