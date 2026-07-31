from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.ml import MlRun, MlPrediction

class MlRunRepositoryInterface(ABC):
    """
    Abstract repository interface managing MlRun entity persistence.
    Why: Decouples service training orchestrations from database transactions.
    """
    @abstractmethod
    def create(self, run: MlRun) -> MlRun:
        """Saves a new ML run configuration and evaluation metrics."""
        pass

    @abstractmethod
    def get_by_id(self, run_id: int) -> Optional[MlRun]:
        """Lookup an ML run record by primary ID."""
        pass

    @abstractmethod
    def list_by_dataset_id(self, dataset_id: int) -> List[MlRun]:
        """List all runs executed over a single dataset ID."""
        pass

class MlPredictionRepositoryInterface(ABC):
    """
    Abstract repository interface managing MlPrediction entity persistence.
    Why: Decouples forecast result records from database transactions.
    """
    @abstractmethod
    def create_batch(self, predictions: List[MlPrediction]) -> List[MlPrediction]:
        """Bulk inserts a batch list of ML predictions points."""
        pass

    @abstractmethod
    def list_by_run_id(self, ml_run_id: int) -> List[MlPrediction]:
        """List all predicted points linked to an ML run instance."""
        pass
