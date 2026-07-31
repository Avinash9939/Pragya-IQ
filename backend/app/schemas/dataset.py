from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.domain.entities.dataset import DatasetStatus

class DatasetOut(BaseModel):
    """
    Schema representing dataset upload meta tracking response.
    Why: Outward schema representation of uploaded datasets.
    """
    id: int
    filename: str
    row_count: int | None
    column_count: int | None
    status: DatasetStatus
    uploaded_at: datetime
    column_mapping: dict | None = None
    columns: list[str] = []

    model_config = ConfigDict(from_attributes=True)
