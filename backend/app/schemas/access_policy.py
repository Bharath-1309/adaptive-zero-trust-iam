import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AccessPolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    effect: Literal["ALLOW", "DENY"]
    priority: int = Field(default=100, ge=0)
    conditions: dict[str, Any]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Policy name cannot be empty.")
        return value


class AccessPolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    effect: Literal["ALLOW", "DENY"] | None = None
    priority: int | None = Field(default=None, ge=0)
    conditions: dict[str, Any] | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Policy name cannot be empty.")
        return value


class AccessPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    effect: str
    priority: int
    conditions: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime