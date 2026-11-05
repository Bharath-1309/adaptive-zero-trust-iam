from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BrowserGPSCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_meters: float = Field(ge=0, le=1_000_000)
    consent_granted: Literal[True]


class LocationObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source: str
    country_code: str | None
    country_name: str | None
    region: str | None
    city: str | None
    latitude: float | None
    longitude: float | None
    accuracy_meters: float | None
    consent_granted: bool
    consent_recorded_at: datetime | None
    observed_at: datetime

class LocationPermissionEventCreate(BaseModel):
    outcome: Literal["GRANTED", "DENIED", "UNAVAILABLE"]
    reason: str | None = None    