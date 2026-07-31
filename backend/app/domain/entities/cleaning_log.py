from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

@dataclass
class CleaningLog:
    """
    Pure domain entity representing a single data cleaning operation trial run.
    Why: Audits datasets cleaning steps history without referencing database frameworks.
    """
    id: int | None
    dataset_id: int
    operation: str
    details: Dict[str, Any]
    executed_at: datetime
