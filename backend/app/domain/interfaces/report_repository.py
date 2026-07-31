from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.report import Report


class ReportRepositoryInterface(ABC):
    """
    Abstract interface for persisting and retrieving PDF report metadata.
    Why: Assures low coupling and high mockability during testing.
    """
    @abstractmethod
    def create(self, report: Report) -> Report:
        pass

    @abstractmethod
    def get_by_id(self, report_id: int) -> Optional[Report]:
        pass
