from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.dataset import Dataset, DatasetStatus

class DatasetRepositoryInterface(ABC):
    """
    Abstract repository interface managing Dataset data lookup and preservation.
    Why: Implements Dependency Inversion so service layers are decoupled from DB models.
    """

    @abstractmethod
    def create(self, dataset: Dataset) -> Dataset:
        """Create a new dataset record in the data storage."""
        pass

    @abstractmethod
    def get_by_id(self, dataset_id: int) -> Optional[Dataset]:
        """Lookup dataset record matching identifier."""
        pass

    @abstractmethod
    def list_by_user(self, user_id: int) -> List[Dataset]:
        """Lookup all datasets owned by a specific user."""
        pass

    @abstractmethod
    def update(self, dataset: Dataset) -> Dataset:
        """Update an existing dataset record in data storage."""
        pass

    @abstractmethod
    def update_status(self, dataset_id: int, status: DatasetStatus) -> Optional[Dataset]:
        """Update dataset status profile in data storage."""
        pass

    @abstractmethod
    def delete(self, dataset_id: int) -> bool:
        """Delete dataset configuration record from DB."""
        pass
