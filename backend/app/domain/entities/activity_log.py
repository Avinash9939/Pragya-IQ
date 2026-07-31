from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ActivityLog:
    """
    Domain entity representing user action logs.
    Why: Log metadata details decoupled from specific DB providers.
    """
    id: Optional[int]
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    timestamp: datetime
