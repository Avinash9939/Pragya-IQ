from dataclasses import dataclass
from datetime import datetime


@dataclass
class SystemSetting:
    """
    Domain entity representing system settings key-value pair.
    Why: Settings metadata details decoupled from specific DB providers.
    """
    key: str
    value: str
    updated_at: datetime
