from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TravelAuthorizationCreate(BaseModel):
    destination: str = Field(min_length=2, max_length=200)
    justification: str = Field(min_length=10, max_length=2000)
    starts_at: datetime
    expires_at: datetime

    @field_validator("destination", "justification")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty.")
        return value

    @field_validator("starts_at", "expires_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Datetime must include a timezone.")
        return value

    @field_validator("expires_at")
    @classmethod
    def validate_expiry(cls, value: datetime, info) -> datetime:
        starts_at = info.data.get("starts_at")
        if starts_at and value <= starts_at:
            raise ValueError("Expiry must be later than the start time.")
        return value


class TravelAuthorizationReview(BaseModel):
    status: Literal["APPROVED", "DENIED"]
    reason: str = Field(min_length=5, max_length=2000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Review reason cannot be empty.")
        return value


class TravelAuthorizationRevoke(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Revocation reason cannot be empty.")
        return value


class TravelAuthorizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    destination: str
    justification: str
    starts_at: datetime
    expires_at: datetime
    status: str
    approved_by_user_id: UUID | None
    approval_reason: str | None
    requested_at: datetime
    reviewed_at: datetime | None
    revoked_at: datetime | None
    revocation_reason: str | None