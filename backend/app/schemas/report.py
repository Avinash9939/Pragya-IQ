from datetime import datetime
from pydantic import BaseModel


class ReportResponse(BaseModel):
    """Response body for report metadata endpoints."""
    id: int
    dataset_id: int
    file_path: str
    generated_at: datetime

    class Config:
        from_attributes = True
