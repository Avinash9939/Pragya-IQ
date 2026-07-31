from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class DatasetStatus(str, Enum):
    """
    Enum representing different processing phases of an uploaded dataset.
    Why: Dictates which downstream operations (cleaning, forecasting, segmentation) are allowed.
    """
    UPLOADED = "UPLOADED"
    VALIDATED = "VALIDATED"
    CLEANED = "CLEANED"
    FEATURED = "FEATURED"
    FAILED = "FAILED"

@dataclass
class Dataset:
    """
    Pure domain Dataset entity tracking storage reference and data dimensional sizing.
    Why: Framework-agnostic definition of a dataset artifact.
    """
    id: int | None
    user_id: int
    filename: str
    storage_path: str
    row_count: int | None
    column_count: int | None
    status: DatasetStatus
    uploaded_at: datetime
    column_mapping: dict | None = None
