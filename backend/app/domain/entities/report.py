from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Report:
    """
    Domain entity representing generated PDF reports.
    Why: Keeps report metadata details decoupled from specific DB providers.
    """
    id: Optional[int]
    dataset_id: int
    file_path: str
    generated_at: datetime
