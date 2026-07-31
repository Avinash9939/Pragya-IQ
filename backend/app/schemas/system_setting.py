from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SystemSettingOut(BaseModel):
    key: str
    value: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemSettingsResponse(BaseModel):
    maintenance_mode: bool = Field(..., description="System maintenance mode status flag")


class SystemSettingsUpdate(BaseModel):
    maintenance_mode: bool = Field(..., description="Update system maintenance mode status flag")
