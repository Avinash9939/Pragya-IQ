from dataclasses import dataclass
from datetime import datetime

@dataclass
class KpiResult:
    """
    Pure domain entity representing a single business KPI computation outcome.
    Why: Framework-agnostic definition of KPI metrics results.
    """
    id: int | None
    dataset_id: int
    kpi_type: str
    value_json: dict
    computed_at: datetime
