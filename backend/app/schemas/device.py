import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegistration(BaseModel):
    device_name: str = Field(min_length=1, max_length=255)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    device_name: str
    operating_system: str | None
    browser: str | None
    is_trusted: bool
    is_active: bool
    last_seen_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime