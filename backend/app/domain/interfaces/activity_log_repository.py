from abc import ABC, abstractmethod
from typing import List, Tuple
from app.domain.entities.activity_log import ActivityLog


class ActivityLogRepositoryInterface(ABC):
    """
    Abstract interface for persisting and retrieving audit logs.
    Why: Assures low coupling and high mockability during testing.
    """
    @abstractmethod
    def create(self, log: ActivityLog) -> ActivityLog:
        pass

    @abstractmethod
    def get_paginated(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> List[ActivityLog]:
        pass
