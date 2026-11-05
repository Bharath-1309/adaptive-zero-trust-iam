from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


LocationType = Literal["PERMANENT", "TEMPORARY"]


class OfficeGeofenceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)

    latitude: Decimal = Field(ge=-90, le=90)
    longitude: Decimal = Field(ge=-180, le=180)

    radius_meters: Decimal = Field(gt=0, le=100000)
    max_accuracy_meters: Decimal = Field(gt=0, le=10000)

    location_type: LocationType = "PERMANENT"
    expires_at: datetime | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Office name cannot be empty.")
        return value

    @field_validator("expires_at")
    @classmethod
    def validate_expiry_timezone(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("Expiry date must include a timezone.")
        return value

    @model_validator(mode="after")
    def validate_location_expiry(self):
        if self.location_type == "PERMANENT" and self.expires_at is not None:
            raise ValueError("Permanent locations cannot have an expiry date.")

        if self.location_type == "TEMPORARY":
            if self.expires_at is None:
                raise ValueError("Temporary locations require an expiry date.")

            if self.expires_at <= datetime.now(timezone.utc):
                raise ValueError("Expiry date must be in the future.")

        return self


class OfficeGeofenceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)

    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    radius_meters: Decimal | None = Field(default=None, gt=0, le=100000)
    max_accuracy_meters: Decimal | None = Field(default=None, gt=0, le=10000)

    location_type: LocationType | None = None
    expires_at: datetime | None = None

    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Office name cannot be empty.")
        return value

    @field_validator("expires_at")
    @classmethod
    def validate_expiry_timezone(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("Expiry date must include a timezone.")
        return value


class OfficeGeofenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    latitude: Decimal
    longitude: Decimal
    radius_meters: Decimal
    max_accuracy_meters: Decimal

    location_type: LocationType
    expires_at: datetime | None

    is_active: bool
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime