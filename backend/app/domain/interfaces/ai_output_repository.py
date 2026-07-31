from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.ai_output import AiOutput


class AiOutputRepositoryInterface(ABC):
    """
    Abstract interface for persisting and retrieving cached business recommendations or summaries.
    Why: Swappable for in-memory testing or different SQL/NoSQL backends.
    """
    @abstractmethod
    def create(self, ai_output: AiOutput) -> AiOutput:
        pass

    @abstractmethod
    def get_latest_by_dataset_and_type(self, dataset_id: int, output_type: str) -> Optional[AiOutput]:
        pass
