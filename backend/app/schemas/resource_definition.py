import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


AccessPolicy = Literal[
    "OFFICE_ONLY",
    "REMOTE_ALLOWED",
    "TRAVEL_ALLOWED",
    "VPN_REQUIRED",
]


class ResourceDefinitionCreate(BaseModel):

    name: str = Field(min_length=1, max_length=255)

    description: str | None = None

    required_permission: str = Field(
        min_length=1,
        max_length=150,
    )

    access_policy: AccessPolicy = "REMOTE_ALLOWED"

    @field_validator("name", "required_permission")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value


class ResourceDefinitionUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    required_permission: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    access_policy: AccessPolicy | None = None

    is_active: bool | None = None

    @field_validator("name", "required_permission")
    @classmethod
    def validate_non_empty_strings(cls, value):
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value


class ResourceDefinitionResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    required_permission: str
    access_policy: AccessPolicy
    requires_office_location: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime