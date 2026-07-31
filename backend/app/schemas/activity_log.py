from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ActivityLogOut(BaseModel):
    """
    Schema representing a single activity log response.
    Why: Dictates JSON naming conventions for API consumers.
    """
    id: int
    user_id: Optional[int] = None
    action: str
    resource: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
