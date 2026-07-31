from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.kpi_result import KpiResult

class KpiResultRepositoryInterface(ABC):
    """
    Abstract repository interface managing KpiResult entity persistence.
    Why: Decouples service processing calculations from DB transactions.
    """

    @abstractmethod
    def create(self, result: KpiResult) -> KpiResult:
        """Saves a new KPI result outcome."""
        pass

    @abstractmethod
    def get_by_dataset_id_and_type(self, dataset_id: int, kpi_type: str) -> Optional[KpiResult]:
        """Lookup stored KPI outcome matching parameters."""
        pass

    @abstractmethod
    def list_by_dataset_id(self, dataset_id: int) -> List[KpiResult]:
        """List all KPI metrics computed for a target dataset."""
        pass
